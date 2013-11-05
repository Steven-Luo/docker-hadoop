#!/usr/bin/env python
import sys
import optparse
from ..app import app
from ..version import VERSION


def main():
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option('-b', '--bind', dest='bind_addr',
                      metavar='ADDR',
                      help='IP addr or hostname to bind to (defaults to 0.0.0.0)')
    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT',
                      help='port to bind to (defaults to 9090)')

    (options, args) = parser.parse_args()

    app.config['BIND_ADDR'] = options.bind_addr or app.config.get('BIND_ADDR', '0.0.0.0')
    app.config['PORT'] = options.port or app.config.get('PORT', 9090)

    print('Docker Hadoop Dashboard, version %s' % VERSION)
    app.run(host=app.config['BIND_ADDR'], port=app.config['PORT'], debug=True)

if __name__ == '__main__':
    main()