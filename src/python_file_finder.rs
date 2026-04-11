use ignore::types::{Types, TypesBuilder};
use ignore::{DirEntry, Walk, WalkBuilder};
use path_slash::PathExt;
use pyo3::{Bound, IntoPyObject, PyAny, PyResult, Python, exceptions::PyValueError, pyfunction};
use regex::Regex;
use std::path::PathBuf;

#[pyfunction]
#[pyo3(signature = (directories, exclude, extend_exclude, using_default_exclude, ignore_notebooks=false))]
pub fn find_python_files(
    py: Python<'_>,
    directories: Vec<PathBuf>,
    exclude: Vec<String>,
    extend_exclude: Vec<String>,
    using_default_exclude: bool,
    ignore_notebooks: bool,
) -> PyResult<Bound<'_, PyAny>> {
    let mut unique_directories = directories;
    unique_directories.dedup();

    let walker = build_walker(
        unique_directories.as_ref(),
        [exclude, extend_exclude].concat().as_ref(),
        using_default_exclude,
        ignore_notebooks,
    )?;

    let python_files: Vec<_> = walker
        .flatten()
        .filter(|entry| entry.path().is_file())
        .map(|entry| {
            entry
                .path()
                .to_string_lossy()
                .strip_prefix("./")
                .unwrap_or(&entry.path().to_string_lossy())
                .to_owned()
        })
        .collect();

    Ok(python_files.into_pyobject(py).unwrap())
}

fn build_walker(
    directories: &[PathBuf],
    excluded_patterns: &[String],
    use_git_ignore: bool,
    ignore_notebooks: bool,
) -> PyResult<Walk> {
    let (first_directory, additional_directories) = directories.split_first().unwrap();

    let mut walk_builder = WalkBuilder::new(first_directory);
    for path in additional_directories {
        walk_builder.add(path);
    }

    let re: Option<Regex> = if excluded_patterns.is_empty() {
        None
    } else {
        Some(
            Regex::new(format!(r"^({})", excluded_patterns.join("|")).as_str())
                .map_err(|err| PyValueError::new_err(format!("Invalid exclude regex: {err}")))?,
        )
    };

    Ok(
        walk_builder
            .types(build_types(ignore_notebooks).unwrap())
            .standard_filters(use_git_ignore)
            .hidden(false)
            .filter_entry(move |entry| entry_satisfies_predicate(entry, re.as_ref()))
            .build(),
    )
}

fn build_types(ignore_notebooks: bool) -> Result<Types, ignore::Error> {
    let mut types_builder = TypesBuilder::new();
    types_builder.add("python", "*.py").unwrap();
    types_builder.select("python");

    if !ignore_notebooks {
        types_builder.add("jupyter", "*.ipynb").unwrap();
        types_builder.select("jupyter");
    }

    types_builder.build()
}

fn entry_satisfies_predicate(entry: &DirEntry, regex: Option<&Regex>) -> bool {
    if regex.is_none() {
        return true;
    }

    let path_str = entry.path().to_slash_lossy();
    !regex
        .unwrap()
        .is_match(path_str.strip_prefix("./").unwrap_or(&path_str).as_ref())
}
