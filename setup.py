from setuptools import setup

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:  # older setuptools
    from wheel.bdist_wheel import bdist_wheel


class BinaryWheel(bdist_wheel):
    """Tag the wheel py3-none-<platform>: pure Python, but ships native binaries."""

    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        _, _, plat = super().get_tag()
        return "py3", "none", plat


setup(cmdclass={"bdist_wheel": BinaryWheel})
