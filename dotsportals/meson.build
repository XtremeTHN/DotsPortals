pkgdatadir = get_option('prefix') / get_option('datadir')
moduledir = pkgdatadir / 'dotsportals'

python = import('python')
python_i = python.find_installation('python3')

conf = configuration_data()
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'xdg-desktop-portal-dotsportals.in',
    output: 'xdg-desktop-portal-dotsportals',
    configuration: conf,
    install: true,
    install_dir: get_option('prefix') / get_option('libexecdir'),
    install_mode: 'r-xr-xr-x'
)

svgtheme_sources = [
    '__init__.py',
    'main.py',
    'quickshell.py',
    'service.py',
    'utils.py',
    'logger.py'
]

install_data(svgtheme_sources, install_dir: moduledir)

subdir('portals')
