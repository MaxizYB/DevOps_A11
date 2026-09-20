#!/usr/bin/env python3
"""Validate the versioned E2 contract examples without third-party packages."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SAMPLES = CONTRACTS / "samples"
JOB_TYPES = {"DRAFT", "FULL_CHECK", "INCREMENTAL_CHECK", "REPAIR"}
STATUSES = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED"}
ARTIFACT_TYPES = {
    "DOCKERFILE",
    "DOCKER_IMAGE",
    "BUILD_LOG",
    "ACTUAL_GRAPH",
    "DECLARED_GRAPH",
    "ERROR_REPORT",
    "PATCH",
    "TEST_RESULT",
}
REQUIRED_ARTIFACTS = {
    "DRAFT": {"DOCKERFILE", "DOCKER_IMAGE", "BUILD_LOG"},
    "FULL_CHECK": {"ACTUAL_GRAPH", "DECLARED_GRAPH", "ERROR_REPORT", "BUILD_LOG"},
    "INCREMENTAL_CHECK": {"ACTUAL_GRAPH", "ERROR_REPORT"},
    "REPAIR": {"PATCH", "BUILD_LOG", "TEST_RESULT", "ERROR_REPORT"},
}
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
TRACE_RE = re.compile(r"^trace-.+")
JOB_ID_RE = re.compile(r"^job-(DRAFT|FULL_CHECK|INCREMENTAL_CHECK|REPAIR)-.+")
ARTIFACT_URI_RE = re.compile(r"^artifact://[^/]+/.+")
CONFIGURATION_RE = re.compile(r"^cfg-[a-z0-9][a-z0-9-]*$")
ERROR_CODE_RE = re.compile(r"^[A-Z]+_[0-9]{4}$")


class ValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def reject(code: str, message: str) -> None:
    raise ValidationError(code, message)


def require_object(value: Any, where: str, code: str = "REQUEST_1001") -> dict[str, Any]:
    if not isinstance(value, dict):
        reject(code, f"{where} must be an object")
    return value


def require_keys(
    value: Any,
    required: set[str],
    allowed: set[str],
    where: str,
    code: str = "REQUEST_1001",
) -> dict[str, Any]:
    data = require_object(value, where, code)
    missing = required - data.keys()
    unexpected = data.keys() - allowed
    if missing:
        reject(code, f"{where} is missing: {', '.join(sorted(missing))}")
    if unexpected:
        reject(code, f"{where} has unexpected fields: {', '.join(sorted(unexpected))}")
    return data


def require_string(value: Any, where: str, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        reject("REQUEST_1001", f"{where} must be a non-empty string")
    if pattern and not pattern.fullmatch(value):
        reject("REQUEST_1001", f"{where} has an invalid format")
    return value


def require_positive_integer(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        reject("REQUEST_1001", f"{where} must be a positive integer")
    return value


def validate_datetime(value: Any, where: str, allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str):
        reject("REQUEST_1001", f"{where} must be an ISO 8601 datetime")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        reject("REQUEST_1001", f"{where} must be an ISO 8601 datetime")


def validate_repository(value: Any, where: str) -> dict[str, Any]:
    repository = require_keys(value, {"url", "commit"}, {"url", "commit"}, where)
    url = require_string(repository["url"], f"{where}.url")
    if not (url.startswith("https://") or url.startswith("http://")):
        reject("REQUEST_1001", f"{where}.url must use HTTP(S)")
    require_string(repository["commit"], f"{where}.commit", COMMIT_RE)
    return repository


def validate_environment(value: Any, where: str) -> dict[str, Any]:
    environment = require_keys(
        value,
        {"image_uri", "configuration_id"},
        {"image_uri", "configuration_id"},
        where,
    )
    require_string(environment["image_uri"], f"{where}.image_uri", ARTIFACT_URI_RE)
    require_string(environment["configuration_id"], f"{where}.configuration_id", CONFIGURATION_RE)
    return environment


def validate_input(job_type: str, value: Any) -> dict[str, Any]:
    if job_type == "DRAFT":
        data = require_keys(
            value,
            {"repository", "build_command", "verify_command", "timeout_seconds"},
            {"repository", "build_command", "verify_command", "max_iterations", "timeout_seconds"},
            "input",
        )
        validate_repository(data["repository"], "input.repository")
        require_string(data["build_command"], "input.build_command")
        require_string(data["verify_command"], "input.verify_command")
        if "max_iterations" in data:
            iterations = require_positive_integer(data["max_iterations"], "input.max_iterations")
            if iterations > 50:
                reject("REQUEST_1001", "input.max_iterations must not exceed 50")
    elif job_type == "FULL_CHECK":
        data = require_keys(
            value,
            {"repository", "environment", "clean_build_command", "project_root", "timeout_seconds"},
            {"repository", "environment", "clean_build_command", "project_root", "timeout_seconds"},
            "input",
        )
        validate_repository(data["repository"], "input.repository")
        validate_environment(data["environment"], "input.environment")
        require_string(data["clean_build_command"], "input.clean_build_command")
        require_string(data["project_root"], "input.project_root")
    elif job_type == "INCREMENTAL_CHECK":
        data = require_keys(
            value,
            {"base_commit", "repository", "baseline", "environment", "build_command", "timeout_seconds"},
            {"base_commit", "repository", "baseline", "environment", "build_command", "timeout_seconds"},
            "input",
        )
        require_string(data["base_commit"], "input.base_commit", COMMIT_RE)
        validate_repository(data["repository"], "input.repository")
        baseline = require_keys(
            data["baseline"],
            {"actual_graph_uri", "commit", "configuration_id"},
            {"actual_graph_uri", "commit", "configuration_id"},
            "input.baseline",
        )
        require_string(baseline["actual_graph_uri"], "input.baseline.actual_graph_uri", ARTIFACT_URI_RE)
        require_string(baseline["commit"], "input.baseline.commit", COMMIT_RE)
        require_string(baseline["configuration_id"], "input.baseline.configuration_id", CONFIGURATION_RE)
        environment = validate_environment(data["environment"], "input.environment")
        require_string(data["build_command"], "input.build_command")
        if baseline["commit"] != data["base_commit"]:
            reject("REQUEST_1002", "input.baseline.commit must equal input.base_commit")
        if baseline["configuration_id"] != environment["configuration_id"]:
            reject(
                "REQUEST_1002",
                "input.baseline.configuration_id must equal input.environment.configuration_id",
            )
    elif job_type == "REPAIR":
        data = require_keys(
            value,
            {
                "repository",
                "md_report_uri",
                "makefile_path",
                "environment",
                "build_command",
                "verify_command",
                "timeout_seconds",
            },
            {
                "repository",
                "md_report_uri",
                "makefile_path",
                "environment",
                "build_command",
                "verify_command",
                "timeout_seconds",
            },
            "input",
        )
        validate_repository(data["repository"], "input.repository")
        require_string(data["md_report_uri"], "input.md_report_uri", ARTIFACT_URI_RE)
        require_string(data["makefile_path"], "input.makefile_path")
        validate_environment(data["environment"], "input.environment")
        require_string(data["build_command"], "input.build_command")
        require_string(data["verify_command"], "input.verify_command")
    else:
        reject("REQUEST_1001", "job_type is not supported")

    require_positive_integer(data["timeout_seconds"], "input.timeout_seconds")
    return data


def validate_create_request(value: Any) -> dict[str, Any]:
    request = require_keys(
        value,
        {"schema_version", "trace_id", "job_type", "idempotency_key", "input"},
        {"schema_version", "trace_id", "job_type", "idempotency_key", "input"},
        "create request",
    )
    require_string(request["schema_version"], "schema_version", VERSION_RE)
    require_string(request["trace_id"], "trace_id", TRACE_RE)
    job_type = require_string(request["job_type"], "job_type")
    if job_type not in JOB_TYPES:
        reject("REQUEST_1001", "job_type is not supported")
    require_string(request["idempotency_key"], "idempotency_key")
    validate_input(job_type, request["input"])
    return request


def validate_execution(value: Any, status: str, timeout_seconds: int) -> None:
    execution = require_keys(
        value,
        {
            "attempt",
            "retry_of_job_id",
            "queued_at",
            "started_at",
            "finished_at",
            "duration_ms",
            "timeout_seconds",
        },
        {
            "attempt",
            "retry_of_job_id",
            "queued_at",
            "started_at",
            "finished_at",
            "duration_ms",
            "timeout_seconds",
        },
        "execution",
    )
    require_positive_integer(execution["attempt"], "execution.attempt")
    if execution["retry_of_job_id"] is not None:
        require_string(execution["retry_of_job_id"], "execution.retry_of_job_id", JOB_ID_RE)
    validate_datetime(execution["queued_at"], "execution.queued_at", allow_null=False)
    validate_datetime(execution["started_at"], "execution.started_at", allow_null=True)
    validate_datetime(execution["finished_at"], "execution.finished_at", allow_null=True)
    if execution["duration_ms"] is not None and (
        isinstance(execution["duration_ms"], bool)
        or not isinstance(execution["duration_ms"], int)
        or execution["duration_ms"] < 0
    ):
        reject("REQUEST_1001", "execution.duration_ms must be a non-negative integer or null")
    if require_positive_integer(execution["timeout_seconds"], "execution.timeout_seconds") != timeout_seconds:
        reject("REQUEST_1001", "execution.timeout_seconds must equal input.timeout_seconds")
    if status in {"SUCCEEDED", "FAILED", "TIMED_OUT"}:
        if execution["started_at"] is None or execution["finished_at"] is None or execution["duration_ms"] is None:
            reject("REQUEST_1001", f"execution fields are incomplete for {status}")
    if status == "CANCELLED" and execution["finished_at"] is None:
        reject("REQUEST_1001", "execution.finished_at is required for CANCELLED")


def validate_artifact(value: Any, job_id: str, commit: str) -> str:
    artifact = require_keys(
        value,
        {"artifact_id", "type", "uri", "media_type", "producer_job_id", "commit", "configuration_id"},
        {"artifact_id", "type", "uri", "media_type", "producer_job_id", "commit", "configuration_id"},
        "output.artifacts[]",
    )
    require_string(artifact["artifact_id"], "artifact.artifact_id")
    artifact_type = require_string(artifact["type"], "artifact.type")
    if artifact_type not in ARTIFACT_TYPES:
        reject("REQUEST_1001", "artifact.type is not supported")
    require_string(artifact["uri"], "artifact.uri", ARTIFACT_URI_RE)
    require_string(artifact["media_type"], "artifact.media_type")
    if artifact["producer_job_id"] != job_id:
        reject("REQUEST_1001", "artifact.producer_job_id must equal job_id")
    if artifact["commit"] != commit:
        reject("REQUEST_1001", "artifact.commit must equal input.repository.commit")
    require_string(artifact["configuration_id"], "artifact.configuration_id", CONFIGURATION_RE)
    return artifact_type


def validate_error(value: Any) -> None:
    error = require_keys(
        value,
        {"code", "message", "retryable", "details", "log_uri"},
        {"code", "message", "retryable", "details", "log_uri"},
        "error",
    )
    require_string(error["code"], "error.code", ERROR_CODE_RE)
    require_string(error["message"], "error.message")
    if not isinstance(error["retryable"], bool):
        reject("REQUEST_1001", "error.retryable must be boolean")
    require_object(error["details"], "error.details")
    if error["log_uri"] is not None:
        require_string(error["log_uri"], "error.log_uri", ARTIFACT_URI_RE)


def validate_response(value: Any) -> dict[str, Any]:
    response = require_keys(
        value,
        {
            "schema_version",
            "job_id",
            "trace_id",
            "job_type",
            "status",
            "execution",
            "input",
            "output",
            "error",
        },
        {
            "schema_version",
            "job_id",
            "trace_id",
            "job_type",
            "status",
            "execution",
            "input",
            "output",
            "error",
        },
        "job response",
    )
    require_string(response["schema_version"], "schema_version", VERSION_RE)
    job_type = require_string(response["job_type"], "job_type")
    if job_type not in JOB_TYPES:
        reject("REQUEST_1001", "job_type is not supported")
    job_id = require_string(response["job_id"], "job_id", JOB_ID_RE)
    if not job_id.startswith(f"job-{job_type}-"):
        reject("REQUEST_1001", "job_id must use the job_type prefix")
    require_string(response["trace_id"], "trace_id", TRACE_RE)
    status = require_string(response["status"], "status")
    if status not in STATUSES:
        reject("REQUEST_1001", "status is not supported")
    input_data = validate_input(job_type, response["input"])
    validate_execution(response["execution"], status, input_data["timeout_seconds"])

    if status == "SUCCEEDED":
        if not isinstance(response["output"], dict) or response["error"] is not None:
            reject("REQUEST_1001", "SUCCEEDED requires output and a null error")
        artifacts = response["output"].get("artifacts")
        if not isinstance(artifacts, list):
            reject("REQUEST_1001", "SUCCEEDED output must contain artifacts")
        artifact_types = {
            validate_artifact(item, job_id, input_data["repository"]["commit"])
            for item in artifacts
        }
        missing = REQUIRED_ARTIFACTS[job_type] - artifact_types
        if missing:
            reject("REQUEST_1001", f"output is missing artifact types: {', '.join(sorted(missing))}")
    elif status in {"FAILED", "TIMED_OUT", "CANCELLED"}:
        if response["output"] is not None or not isinstance(response["error"], dict):
            reject("REQUEST_1001", f"{status} requires null output and an error")
        validate_error(response["error"])
    elif response["output"] is not None or response["error"] is not None:
        reject("REQUEST_1001", f"{status} requires null output and error")
    return response


def validate_schema_files() -> int:
    schema_paths = sorted((CONTRACTS / "schemas").glob("*.json"))
    if len(schema_paths) != 2:
        raise RuntimeError("expected exactly two E2 schema files")
    for path in schema_paths:
        schema = load_json(path)
        if not isinstance(schema, dict) or "$schema" not in schema or "$defs" not in schema:
            raise RuntimeError(f"{path.relative_to(ROOT)} is not an E2 JSON Schema document")
        print(f"PASS schema: {path.relative_to(ROOT)}")
    return len(schema_paths)


def validate_samples() -> int:
    pairs = {
        "draft": ("draft-create.json", "draft-succeeded.json"),
        "full-check": ("full-check-create.json", "full-check-succeeded.json"),
        "incremental-check": ("incremental-check-create.json", "incremental-check-succeeded.json"),
        "repair": ("repair-create.json", "repair-succeeded.json"),
    }
    count = 0
    for name, (request_name, response_name) in pairs.items():
        request = validate_create_request(load_json(SAMPLES / "requests" / request_name))
        response = validate_response(load_json(SAMPLES / "responses" / response_name))
        if request["job_type"] != response["job_type"]:
            raise RuntimeError(f"{name} request and response have different job types")
        for field, value in request["input"].items():
            if response["input"].get(field) != value:
                raise RuntimeError(f"{name} response input does not preserve {field}")
        print(f"PASS exchange: {name}")
        count += 1
    return count


def validate_invalid_samples() -> int:
    expected_codes = {
        "unknown-job-type.json": "REQUEST_1001",
        "incremental-check-missing-baseline.json": "REQUEST_1001",
        "incremental-check-mismatched-baseline.json": "REQUEST_1002",
    }
    count = 0
    for filename, expected_code in expected_codes.items():
        try:
            validate_create_request(load_json(SAMPLES / "invalid" / filename))
        except ValidationError as error:
            if error.code != expected_code:
                raise RuntimeError(
                    f"{filename} returned {error.code}, expected {expected_code}: {error}"
                ) from error
            print(f"PASS rejection: {filename} -> HTTP 400 / {error.code}")
            count += 1
        else:
            raise RuntimeError(f"{filename} was accepted unexpectedly")
    return count


def validate_failure_samples() -> int:
    response = validate_response(load_json(SAMPLES / "responses" / "full-check-failed.json"))
    if response["status"] != "FAILED" or response["output"] is not None:
        raise RuntimeError("full-check-failed.json does not express a failed job")
    if response["error"]["code"] != "ANALYSIS_5001":
        raise RuntimeError("full-check-failed.json must use ANALYSIS_5001")
    print("PASS failed job: full-check-failed.json -> FAILED / ANALYSIS_5001")
    return 1


def main() -> int:
    try:
        schema_count = validate_schema_files()
        exchange_count = validate_samples()
        failure_count = validate_failure_samples()
        rejection_count = validate_invalid_samples()
    except (OSError, json.JSONDecodeError, RuntimeError, ValidationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "PASS contract validation: "
        f"{schema_count} schemas, {exchange_count} exchanges, "
        f"{failure_count} failed job, {rejection_count} rejections"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
