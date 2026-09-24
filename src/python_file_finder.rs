use ignore::types::{Types, TypesBuilder};
use ignore::{DirEntry, Walk, WalkBuilder};
use path_slash::PathExt;
use pyo3::{Bound, IntoPyObject, PyAny, Python, pyfunction};
use regex::Regex;
use std::path::PathBuf;

fn _build_single_file_result(unique_paths: &[PathBuf], ignore_notebooks: bool) -> Vec<String> {
    let var_name = &unique_paths[0];
    let path = var_name;
    let is_valid = match path.extension().and_then(|ext| ext.to_str()) {
        Some("py") => true,
        Some("ipynb") => !ignore_notebooks,
        _ => false,
    };

    let result: Vec<String> = if is_valid {
        let path_str = path.to_string_lossy();
        vec![path_str.strip_prefix("./").unwrap_or(&path_str).to_string()]
    } else {
        vec![]
    };

    result
}

#[pyfunction]
#[pyo3(signature = (paths, exclude, extend_exclude, using_default_exclude, ignore_notebooks=false))]
pub fn find_python_files(
    py: Python<'_>,
    paths: Vec<PathBuf>,
    exclude: Vec<String>,
    extend_exclude: Vec<String>,
    using_default_exclude: bool,
    ignore_notebooks: bool,
) -> Bound<'_, PyAny> {
    let mut unique_paths: Vec<PathBuf> = paths;
    unique_paths.dedup();

    // Fast Path: If there's only one file passed
    let is_single_file: bool = unique_paths.len() == 1 && unique_paths[0].is_file();
    if is_single_file {
        return _build_single_file_result(&unique_paths, ignore_notebooks)
            .into_pyobject(py)
            .unwrap();
    }

    // General Path: Multiple files or directories
    build_walker(
        unique_paths.as_ref(),
        [exclude, extend_exclude].concat().as_ref(),
        using_default_exclude,
        ignore_notebooks,
    )
    .flatten()
    .filter(|entry| entry.path().is_file())
    .map(|entry| {
        let path_str = entry.path().to_string_lossy();
        path_str.strip_prefix("./").unwrap_or(&path_str).to_string()
    })
    .collect::<Vec<String>>()
    .into_pyobject(py)
    .unwrap()
}

fn build_walker(
    directories: &[PathBuf],
    excluded_patterns: &[String],
    use_git_ignore: bool,
    ignore_notebooks: bool,
) -> Walk {
    let (first_directory, additional_directories) = directories.split_first().unwrap();

    let mut walk_builder = WalkBuilder::new(first_directory);
    for path in additional_directories {
        walk_builder.add(path);
    }

    let re: Option<Regex> = if excluded_patterns.is_empty() {
        None
    } else {
        Some(Regex::new(format!(r"^({})", excluded_patterns.join("|")).as_str()).unwrap())
    };

    walk_builder
        .types(build_types(ignore_notebooks).unwrap())
        .standard_filters(use_git_ignore)
        .hidden(false)
        .filter_entry(move |entry| entry_satisfies_predicate(entry, re.as_ref()))
        .build()
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
