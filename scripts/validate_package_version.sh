# This script checks if the package version of a locally build
# Python package residing in the dist/ subdirectory matches
# the latest git version tag and aborts with an
# exit 1 if not.
#
# The script is meant to be used in github workflow to
# check a generated package before deploying.
#
function validate_package_version() {

  git fetch --all --tags

  git_ref=$1
  echo "Git ref: ${git_ref}"
  input_branch="${git_ref}"
  echo "Input branch: ${input_branch}"
  branch_head_commit_id=$(git rev-parse ${input_branch})
  echo "Head commit: ${branch_head_commit_id}"
  latest_git_tag=$(git describe --tags ${branch_head_commit_id})
  echo "Latest tag: ${latest_git_tag}"
  version=${latest_git_tag#v} # remove the prefix "v"
  echo "Version: ${version}"
  package_archive="dist/elf_diff-${version}.tar.gz"
  echo "Expected package archive: ${package_archive}"

  if [ ! -f "${package_archive}" ]; then
    echo "Package archive file ${package_archive} not found!"
    echo "Found instead:"
    echo $(ls -l dist)
    exit 1
  fi
}

# Use this function to validate a generated Python package
# to check if its version is based on the latest git tag.
# The tag must not necessarily point to the HEAD commit.
#
function validate_package_version_wo_sha() {

  git fetch --all --tags

  git_ref=$1
  echo "Git ref: ${git_ref}"
  input_branch="${git_ref}"
  echo "Input branch: ${input_branch}"
  branch_head_commit_id=$(git rev-parse ${input_branch}) # Do not append the git sha to the rev-parse output
  echo "Head commit: ${branch_head_commit_id}"
  latest_git_tag=$(git describe --tags --abbrev=0 ${branch_head_commit_id})
  echo "Latest tag: ${latest_git_tag}"
  version=${latest_git_tag#v} # remove the prefix "v"
  echo "Version: ${version}"
  package_archive="dist/elf_diff-${version}.tar.gz"
  echo "Expected package archive: ${package_archive}"

  if [ ! -f "${package_archive}" ]; then
    echo "Package archive file ${package_archive} not found!"
    echo "Found instead:"
    echo $(ls -l dist)
    exit 1
  fi
}
