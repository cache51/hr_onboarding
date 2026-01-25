from setuptools import setup, find_packages

setup(
    name="hr_onboarding",
    version="0.0.1",
    description="Custom fields for HR onboarding mobile app",
    author="RGM",
    author_email="admin@rgm.vn",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["frappe"],
)
