datadir = get_option('datadir')
prefix = get_option('prefix')

install_data(
    'dotsportals.portal',
    install_dir: datadir / 'xdg-desktop-portal' / 'portals'
)

conf_data = configuration_data()
conf_data.set('BINARY_PATH', prefix / get_option('libexecdir') / meson.project_name())

basename = 'org.freedesktop.impl.portal.desktop.dotsportals.service'
configure_file(
    configuration: conf_data,
    input: basename + '.in',
    output: basename,
    install: true,
    install_dir: prefix / datadir / 'dbus-1' / 'services'
)
