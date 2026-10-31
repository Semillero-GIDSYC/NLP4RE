import { Component, OnDestroy, OnInit, input, signal } from '@angular/core';

@Component({
  selector: 'app-typewriter',
  template: `{{ displayed() }}@if (typing()) {<span class="inline-block w-1.5 h-3.5 bg-blue-900 ml-0.5 animate-pulse align-middle"></span>}`
})
export class TypewriterComponent implements OnInit, OnDestroy {
  readonly text = input('');
  readonly speed = input(10);  // ms por carácter

  readonly displayed = signal('');
  readonly typing = signal(true);
  private timer?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    // Empieza a escribir apenas aparece; se calcula con el tiempo real para no desfasarse
    const start = Date.now();
    this.timer = setInterval(() => {
      const full = this.text();
      const chars = Math.floor((Date.now() - start) / this.speed());
      this.displayed.set(full.slice(0, chars));
      if (chars >= full.length) {
        this.typing.set(false);
        clearInterval(this.timer);
      }
    }, 16);
  }

  ngOnDestroy(): void {
    clearInterval(this.timer);
  }
}
