import { describe, it, expect } from "vitest";
import { hasProjectRole } from "./permissions";
import type { ProjectRole } from "../types";

describe("hasProjectRole", () => {
  it("powinien zwrocic true, gdy uzytkownik posiada dokladnie jedna z wymaganych rol", () => {
    const userRoles = ["developer"] as ProjectRole[];
    const allowedRoles = ["developer", "scrum_master"] as ProjectRole[];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(true);
  });

  it("powinien zwrocic true, gdy uzytkownik posiada wiele rol i przynajmniej jedna pasuje", () => {
    const userRoles = ["developer", "project_owner", "maintainer"] as ProjectRole[];
    const allowedRoles = ["project_owner"] as ProjectRole[];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(true);
  });

  it("powinien zwrocic false, gdy uzytkownik nie posiada zadnej z wymaganych rol", () => {
    const userRoles = ["developer", "qa"] as ProjectRole[];
    const allowedRoles = ["scrum_master", "project_owner"] as ProjectRole[];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(false);
  });

  it("powinien zwrocic false, gdy uzytkownik nie ma zadnych rol", () => {
    const userRoles: ProjectRole[] = [];
    const allowedRoles = ["developer"] as ProjectRole[];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(false);
  });

  it("powinien zwrocic false, gdy lista dopuszczalnych rol jest pusta", () => {
    const userRoles = ["project_owner"] as ProjectRole[];
    const allowedRoles: ProjectRole[] = [];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(false);
  });

  it("powinien poprawnie sprawdzic role przy identycznych tablicach", () => {
    const userRoles = ["scrum_master", "developer"] as ProjectRole[];
    const allowedRoles = ["scrum_master", "developer"] as ProjectRole[];
    
    expect(hasProjectRole(userRoles, allowedRoles)).toBe(true);
  });
});