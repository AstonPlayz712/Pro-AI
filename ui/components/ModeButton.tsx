"use client";

/** Single button used by the sidebar for selecting a mode. */

import React from "react";

export type ModeButtonProps = {
  label: string;
  isActive?: boolean;
  onClick?: () => void;
};

export function ModeButton({ label, isActive = false, onClick }: ModeButtonProps): React.JSX.Element {
  return (
    <button
      type="button"
      className={`vsc-mode-button${isActive ? " is-active" : ""}`}
      aria-pressed={isActive}
      onClick={onClick}
    >
      <span className="vsc-mode-button__label">{label}</span>
    </button>
  );
}
