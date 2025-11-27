import {
  refineDataProvider,
  refineResources,
  refineOptions,
  refineRouterProvider,
} from "../refine";

describe("refineDataProvider", () => {
  describe("getList", () => {
    it("throws helpful error with resource name", async () => {
      await expect(
        refineDataProvider.getList({
          resource: "users",
        })
      ).rejects.toThrow('Data provider not configured. Attempted getList for "users".');
    });

    it("includes setup instructions in error", async () => {
      await expect(
        refineDataProvider.getList({
          resource: "users",
        })
      ).rejects.toThrow("See lib/refine.tsx and ARCHITECTURE.md for setup instructions.");
    });
  });

  describe("getOne", () => {
    it("throws helpful error with resource and id", async () => {
      await expect(
        refineDataProvider.getOne({
          resource: "users",
          id: 1,
          meta: {},
        })
      ).rejects.toThrow('Attempted getOne for "users" with id "1"');
    });
  });

  describe("create", () => {
    it("throws helpful error", async () => {
      await expect(
        refineDataProvider.create({
          resource: "users",
          variables: { name: "Test" },
          meta: {},
        })
      ).rejects.toThrow('Attempted create for "users"');
    });
  });

  describe("update", () => {
    it("throws helpful error with resource and id", async () => {
      await expect(
        refineDataProvider.update({
          resource: "users",
          id: 1,
          variables: { name: "Updated" },
          meta: {},
        })
      ).rejects.toThrow('Attempted update for "users" with id "1"');
    });
  });

  describe("deleteOne", () => {
    it("throws helpful error with resource and id", async () => {
      await expect(
        refineDataProvider.deleteOne({
          resource: "users",
          id: 1,
          meta: {},
        })
      ).rejects.toThrow('Attempted deleteOne for "users" with id "1"');
    });
  });

  describe("getApiUrl", () => {
    it("returns empty string", () => {
      expect(refineDataProvider.getApiUrl()).toBe("");
    });
  });
});

describe("refineResources", () => {
  it("starts as an empty array", () => {
    expect(refineResources).toEqual([]);
  });

  it("is an array", () => {
    expect(Array.isArray(refineResources)).toBe(true);
  });
});

describe("refineOptions", () => {
  it("has correct default options", () => {
    expect(refineOptions.syncWithLocation).toBe(true);
    expect(refineOptions.warnWhenUnsavedChanges).toBe(true);
    expect(refineOptions.useNewQueryKeys).toBe(true);
    expect(refineOptions.projectId).toBe("refine-dashboard");
  });
});

describe("refineRouterProvider", () => {
  it("is defined", () => {
    expect(refineRouterProvider).toBeDefined();
  });
});
