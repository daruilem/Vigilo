/** Stand-in for the browser's EventSource: tests push server events by hand. */
export class FakeEventSource {
  static last: FakeEventSource;
  url: string;
  closed = false;
  onerror: (() => void) | null = null;
  private listeners: Record<string, ((event: MessageEvent<string>) => void)[]> = {};

  constructor(url: string) {
    this.url = url;
    FakeEventSource.last = this;
  }

  addEventListener(type: string, listener: (event: MessageEvent<string>) => void) {
    (this.listeners[type] ??= []).push(listener);
  }

  emit(type: string, data: unknown) {
    for (const listener of this.listeners[type] ?? []) {
      listener(new MessageEvent(type, { data: JSON.stringify(data) }));
    }
  }

  close() {
    this.closed = true;
  }
}
