# package.py

import argparse
import os
import subprocess
import sys
import toml
from dotenv import load_dotenv


def get_current_version():
    """Get the current version from pyproject.toml"""
    try:
        pyproject = toml.load("pyproject.toml")
        return pyproject["tool"]["poetry"]["version"]
    except (FileNotFoundError, KeyError) as e:
        print(f"Error reading version from pyproject.toml: {e}")
        sys.exit(1)


def update_version(current_version, release_type):
    """Calculate the new version number based on release type (major, minor, patch)"""
    major, minor, patch = map(int, current_version.split("."))
    
    if release_type == "major":
        return f"{major + 1}.0.0"
    elif release_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif release_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"Invalid release type: {release_type}")
        sys.exit(1)


def run_command(command, error_message):
    """Run a shell command and handle errors"""
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{error_message}: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return False


def main():
    # Load environment variables from .env file
    if load_dotenv():
        print("Loaded environment variables from .env file")
    
    parser = argparse.ArgumentParser(description="Release a new version of the library")
    parser.add_argument(
        "release_type",
        choices=["major", "minor", "patch"],
        help="Type of release (major, minor, or patch)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Print what would happen without making changes"
    )
    
    args = parser.parse_args()
    
    # Check for GitHub credentials
    github_username = os.environ.get("GITHUB_USERNAME")
    github_token = os.environ.get("GITHUB_TOKEN")
    
    if not args.dry_run and (not github_username or not github_token):
        print("Error: GITHUB_USERNAME and/or GITHUB_TOKEN environment variables not found.")
        print("These are required for publishing to GitHub Packages.")
        print("Please create a .env file with these variables or set them in your environment.")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Calculate new version
    new_version = update_version(current_version, args.release_type)
    print(f"New version will be: {new_version}")
    
    if args.dry_run:
        print("Dry run complete. No changes made.")
        return
    
    # Tag the current commit with the new version
    tag_name = f"v{new_version}"
    if not run_command(
        ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"],
        "Failed to create git tag"
    ):
        sys.exit(1)
    
    # Push the tag to GitHub
    if not run_command(
        ["git", "push", "origin", tag_name],
        "Failed to push tag"
    ):
        sys.exit(1)
    
    # Temporarily update pyproject.toml version for building
    try:
        # Load the pyproject.toml
        pyproject = toml.load("pyproject.toml")
        
        # Store the original version
        original_version = pyproject["tool"]["poetry"]["version"]
        
        # Update the version
        pyproject["tool"]["poetry"]["version"] = new_version
        
        # Write the updated pyproject.toml
        with open("pyproject.toml", "w") as f:
            toml.dump(pyproject, f)
        
        # Build the package
        if not run_command(
            ["poetry", "build"],
            "Failed to build package"
        ):
            # Restore original version on failure
            pyproject["tool"]["poetry"]["version"] = original_version
            with open("pyproject.toml", "w") as f:
                toml.dump(pyproject, f)
            sys.exit(1)
        
        # Configure GitHub Packages repository if needed
        if not run_command(
            ["poetry", "config", "repositories.github", "https://github.com/anotherbazeinthewall/chatline-interface"],
            "Failed to configure GitHub repository"
        ):
            sys.exit(1)
        
        # Publish to GitHub Packages
        if not run_command(
            ["poetry", "publish", "--repository", "github", "--username", github_username, "--password", github_token],
            "Failed to publish package"
        ):
            sys.exit(1)
        
        # Restore the original version in pyproject.toml
        pyproject["tool"]["poetry"]["version"] = original_version
        with open("pyproject.toml", "w") as f:
            toml.dump(pyproject, f)
            
    except Exception as e:
        print(f"Error handling pyproject.toml: {e}")
        sys.exit(1)
    
    print(f"\nSuccessfully released version {new_version}!")
    print(f"\nTo install this package:")
    print(f"pip install chatline --index-url https://github.com/anotherbazeinthewall/chatline-interface")


if __name__ == "__main__":
    main()