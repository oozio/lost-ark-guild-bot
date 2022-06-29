from distutils.core import setup, Extension


def main():
    module_1 = Extension('honing_cpp', sources=['honing_cpp.cpp'])

    setup(name='LostArkTraderPackage',
          version='1.0.0',
          description='Package for the Trader guild Discord bot.',
          ext_modules=[module_1])


if __name__ == '__main__':
    main()
