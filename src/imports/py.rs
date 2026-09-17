use crate::file_utils;
use crate::location;

use super::shared;
use file_utils::read_file;
use location::Location;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use rayon::prelude::*;
use regex::Regex;
use ruff_text_size::TextRange;
use std::collections::HashMap;
use std::sync::LazyLock;

/// Canonical implementation of inline script metadata
/// from <https://packaging.python.org/en/latest/specifications/inline-script-metadata/#specification>.
static INLINE_SCRIPT_METADATA_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$").unwrap()
});

/// Processes multiple Python files in parallel to extract import statements and their locations.
/// Accepts a list of file paths and returns a dictionary mapping module names to their import locations.
#[pyfunction]
pub fn get_imports_from_py_files(py: Python<'_>, file_paths: Vec<String>) -> Bound<'_, PyDict> {
    let results: Vec<_> = file_paths
        .par_iter()
        .map(|path_str| {
            let result = get_imports_from_py_file(path_str);
            shared::ThreadResult {
                file: path_str.to_string(),
                result,
            }
        })
        .collect();

    let (all_imports, errors) = shared::merge_results_from_threads(results);
    shared::log_python_errors_as_warnings(&errors);

    all_imports.into_pyobject(py).unwrap()
}

/// Core helper function that extracts import statements and their locations from the content of a single Python file.
/// Used internally by both parallel and single file processing functions.
/// Files using inline script
/// metadata (<https://packaging.python.org/en/latest/specifications/inline-script-metadata/>) are skipped, as those
/// files are self-contained, and as such, imports in those files should be ignored.
fn get_imports_from_py_file(path_str: &str) -> PyResult<HashMap<String, Vec<Location>>> {
    let file_content = read_file(path_str)?;

    // Ignore imports from files using inline script metadata, as they are self-contained.
    let imported_modules: HashMap<String, Vec<TextRange>> = if INLINE_SCRIPT_METADATA_REGEX
        .captures(&file_content)
        .is_none()
    {
        let ast = shared::parse_file_content(&file_content)?;
        shared::extract_imports_from_parsed_file_content(ast)
    } else {
        HashMap::new()
    };

    Ok(shared::convert_imports_with_textranges_to_location_objects(
        imported_modules,
        path_str,
        &file_content,
    ))
}
