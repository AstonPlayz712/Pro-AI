export type AiMode = "local" | "cloud" | "hybrid";

export class AiModeManager {
  public defaultMode: AiMode;
  public currentMode: AiMode;

  constructor(initial: AiMode = "hybrid") {
    this.defaultMode = initial;
    this.currentMode = initial;
  }

  setDefaultMode(mode: AiMode) {
    this.defaultMode = mode;
    this.currentMode = mode;
  }

  temporarilyUse(mode: AiMode) {
    this.currentMode = mode;
  }

  resetToDefault() {
    this.currentMode = this.defaultMode;
  }
}
