"""Small Prometheus counters for the opt-in microservice deployment."""

from datetime import datetime, timezone
import json
from threading import Lock


class Metrics:
    def __init__(self, prefix, label):
        self.prefix = prefix
        self.label = label
        self.lock = Lock()
        self.values = {status: (0, 0.0) for status in ('succeeded', 'failed', 'timed_out')}

    def observe(self, status, seconds):
        with self.lock:
            count, total = self.values[status.lower()]
            self.values[status.lower()] = count + 1, total + seconds

    def render(self):
        with self.lock:
            items = list(self.values.items())
        counter = self.prefix + '_total'
        duration = self.prefix + '_duration_seconds'
        lines = [f'# TYPE {counter} counter']
        for status, (count, _) in items:
            lines.append(f'{counter}{{{self.label},status="{status}"}} {count}')
        lines.append(f'# TYPE {duration} summary')
        for status, (count, seconds) in items:
            labels = f'{{{self.label},status="{status}"}}'
            lines.extend((f'{duration}_sum{labels} {seconds}', f'{duration}_count{labels} {count}'))
        return '\n'.join(lines) + '\n'


def log(service, event, **fields):
    print(json.dumps(dict(timestamp=datetime.now(timezone.utc).isoformat(),
                          service=service, event=event, **fields), ensure_ascii=False), flush=True)
