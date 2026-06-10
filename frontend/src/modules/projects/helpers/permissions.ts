import type { ProjectRole } from "../types";

export function hasProjectRole(
  roles: ProjectRole[],
  allowed: ProjectRole[],
): boolean {
  return allowed.some((role) =>
    roles.includes(role),
  );
}

// EXAMPLE USAGE:
// export default function ExamplePanel() {
// const { project } = useOutletContext<OutletContext>();

// const canManageXYZ = hasProjectRole(
//     project.currentUserRoles,
//     ["ROLE_1", "ROLE_2"],
// );
