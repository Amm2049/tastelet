import { describe, expect, it } from "vitest";

import { MAX_PICKS, canSubmit, counterText, togglePick } from "./picks.js";

const pickedIds = (count) => Array.from({ length: count }, (_, i) => i + 1);

describe("togglePick", () => {
  it("adds a movie that is not picked yet", () => {
    expect(togglePick([1, 2], 3)).toEqual([1, 2, 3]);
  });

  it("removes a movie that is already picked", () => {
    expect(togglePick([1, 2, 3], 2)).toEqual([1, 3]);
  });

  it("does not add an 11th movie", () => {
    const tenPicks = pickedIds(MAX_PICKS);
    expect(togglePick(tenPicks, 99)).toBe(tenPicks);
  });

  it("still removes a movie when at the maximum", () => {
    expect(togglePick(pickedIds(MAX_PICKS), 10)).toEqual(pickedIds(9));
  });
});

describe("canSubmit", () => {
  it.each([
    [4, false],
    [5, true],
    [10, true],
    [11, false],
  ])("%i picks -> %s", (count, expected) => {
    expect(canSubmit(pickedIds(count))).toBe(expected);
  });
});

describe("counterText", () => {
  it.each([
    [0, "0/5"],
    [4, "4/5"],
    [5, "5/10"],
    [10, "10/10"],
  ])("%i picks -> %s", (count, expected) => {
    expect(counterText(pickedIds(count))).toBe(expected);
  });
});
