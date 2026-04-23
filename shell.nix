{
  pkgs ? import <nixpkgs> { },
  pyproject-nix ?
    import
      (pkgs.fetchFromGitHub {
        owner = "pyproject-nix";
        repo = "pyproject.nix";
        rev = "69f57f27e52a87c54e28138a75ec741cd46663c9";
        hash = "sha256-Gs1VnEkCkkRZxJQAC/Dhz0Jbfi22mFXChbtNg9w/Ybg=";
      })
      {
        inherit (pkgs) lib;
      },
}:
let
  python = pkgs.python313;
  project = pyproject-nix.lib.project.loadPyproject { projectRoot = ./backend; };
  pythonEnv =
    assert project.validators.validateVersionConstraints { inherit python; } == { };
    (python.withPackages (project.renderers.withPackages { inherit python; }));
in
pkgs.mkShell {
  packages = [
    pythonEnv
    pkgs.nodejs
  ];
}
