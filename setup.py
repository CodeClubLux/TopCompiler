from setuptools import setup

setup(name='TopCompiler',
      version='0.2',
      description='Compiler for Top programming language',
      url='https://github.com/CodeClubLux/TopCompiler',
      author='CompilerLuke',
      author_email="lgoetz@islux.lu",
      scripts= ["bin/topc", "bin/topdev", "bin/port.py", "bin/port", "bin/topr", "bin/topc.py", "bin/topr.py", "bin/topdev.py"],
      license='MIT',
      zip_safe=False,
      packages= ["TopCompiler","AST", "optimization"],
      install_requires=[
            "Flask",
            "Flask-SocketIO",
            "requests",
            "jsbeautifier",
            "pypandoc"
      ],
      include_package_data=True,
      classifiers=[
            'Development Status :: 3 - Alpha',
      ],
      keywords="top top-lang compiler transpiler",
      python_requires='>=3',
)