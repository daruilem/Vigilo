import type { OwnershipChallenge } from "./types";

/**
 * A verification code waiting to be published, kept in this browser so the owner can
 * forward the request, close the page and come back later. Only the code is kept (it is
 * meant to be published anyway), and it is removed once verified or expired.
 */

const PREFIX = "vigilo.proof.";

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function saveChallenge(target: string, challenge: OwnershipChallenge): void {
  try {
    storage()?.setItem(PREFIX + target, JSON.stringify(challenge));
  } catch {
    // Storage full or refused: the code simply is not remembered.
  }
}

export function forgetChallenge(target: string): void {
  try {
    storage()?.removeItem(PREFIX + target);
  } catch {
    // Nothing was kept.
  }
}

export function loadChallenge(target: string, now: number = Date.now()): OwnershipChallenge | null {
  let raw: string | null = null;
  try {
    raw = storage()?.getItem(PREFIX + target) ?? null;
  } catch {
    return null;
  }
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as OwnershipChallenge;
    const valid =
      typeof value?.token === "string" &&
      typeof value.domain === "string" &&
      typeof value.expires_at === "number" &&
      typeof value.meta?.tag === "string" &&
      typeof value.file?.name === "string" &&
      typeof value.file?.url === "string" &&
      typeof value.dns?.name === "string" &&
      typeof value.dns?.value === "string";
    if (valid && value.expires_at * 1000 > now) return value;
  } catch {
    // Unreadable: forget it below.
  }
  forgetChallenge(target);
  return null;
}
