use chardetng::{EncodingDetector, Iso2022JpDetection, Utf8Detection};
use encoding_rs::Encoding;
use pyo3::exceptions::{PyFileNotFoundError, PyIOError};
use pyo3::prelude::*;
use regex::Regex;
use std::fs;
use std::fs::File;
use std::io::{BufReader, ErrorKind, Read};
use std::path::Path;

/// Reads a Python file's content as a `String`. It first attempts to read the file as UTF-8.
/// If reading fails due to an encoding issue, it tries to determine the file's encoding
/// from a Python encoding declaration or by guessing and then reads the file using the detected encoding
pub fn read_file(file_path: &str) -> PyResult<String> {
    let path = Path::new(file_path);

    match fs::read_to_string(path) {
        Ok(content) => Ok(content),
        Err(e) => match e.kind() {
            ErrorKind::NotFound => Err(PyFileNotFoundError::new_err(format!(
                "File not found: '{file_path}'",
            ))),
            ErrorKind::InvalidData => {
                let file = File::open(path).unwrap();
                let mut buffer = Vec::new();
                BufReader::new(file).read_to_end(&mut buffer)?;

                let encoding = detect_python_file_encoding_from_regex(&buffer)
                    .unwrap_or_else(|| guess_encoding(&buffer));
                read_with_encoding(&buffer, encoding)
            }
            _ => Err(PyIOError::new_err(format!("An error occurred: '{e}'"))),
        },
    }
}

/// Detects the encoding declared in the first or second line of a Python file according to PEP 263.
/// Returns the detected encoding if found; otherwise, returns None.
fn detect_python_file_encoding_from_regex(buffer: &[u8]) -> Option<&'static Encoding> {
    let content = String::from_utf8_lossy(buffer);
    let re = Regex::new(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)").unwrap();

    for line in content.lines().take(2) {
        if let Some(caps) = re.captures(line)
            && let Some(m) = caps.get(1)
        {
            return Encoding::for_label(m.as_str().as_bytes());
        }
    }

    None
}

/// Reads the content of a buffer using the specified encoding and returns the content as a `String`.
/// If decoding fails, it returns an error indicating that decoding was unsuccessful.
fn read_with_encoding(buffer: &[u8], encoding: &'static Encoding) -> PyResult<String> {
    let (cow, _encoding_used, had_errors) = encoding.decode(buffer);
    if had_errors {
        return Err(PyIOError::new_err(
            "Failed to decode file content with the detected encoding.",
        ));
    }
    Ok(cow.into_owned())
}

/// Uses the `EncodingDetector` crate to guess the encoding of a given byte array.
/// Returns the guessed encoding, defaulting to UTF-8 if no conclusive guess can be made.
fn guess_encoding(bytes: &[u8]) -> &'static Encoding {
    let mut detector = EncodingDetector::new(Iso2022JpDetection::Deny);
    detector.feed(bytes, true);
    detector.guess(None, Utf8Detection::Allow)
}
