# Contracts

This directory contains versioned, shared contracts for A11 and its paired group.

For E2, use the following artifacts together:

- [E2 interface contract](e2-interface-contract.md): the normative human-readable agreement for the four services.
- `schemas/`: machine-readable JSON Schema definitions for creation requests and job responses.
- `samples/`: valid and invalid exchange examples used by the contract validator.
- `../scripts/validate_contract.py`: dependency-free validation for the E2 examples and cross-field rules that JSON Schema alone cannot express.

All changes must be made through the Issue that owns the agreement and must follow `docs/A11组协作规范.md`.
