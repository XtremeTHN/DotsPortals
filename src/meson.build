cargo = find_program('cargo')

if get_option('buildtype') == 'release'
  cargo_profile = 'release'
  cargo_args = ['--release']
else
  cargo_profile = 'debug'
  cargo_args = []
endif

cargo_target_dir = meson.project_build_root() / 'cargo-target'

custom_target(
  meson.project_name(),
  build_by_default: true,
  build_always_stale: true,
  console: true,
  output: 'xdg-desktop-portal-dotsportals',
  install: true,
  install_dir: get_option('libexecdir'),
  command: [
    'env', 'CARGO_TARGET_DIR=' + cargo_target_dir,
    cargo, 'build', '--manifest-path', meson.project_source_root() / 'Cargo.toml',
    cargo_args,
    '&&', 'cp', cargo_target_dir / cargo_profile / meson.project_name(), '@OUTPUT@',
  ],
)
