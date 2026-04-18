use ruff_python_ast::visitor::{Visitor, walk_stmt};
use ruff_python_ast::{
    self, Expr, ExprAttribute, ExprName, Stmt, StmtExpr, StmtIf, StmtImport, StmtImportFrom,
};
use ruff_text_size::TextRange;
use std::collections::{HashMap, HashSet};

#[derive(Debug, Clone)]
pub struct ImportVisitor {
    imports: HashMap<String, Vec<TextRange>>,
    import_module_names: HashSet<String>,
    typing_aliases: HashSet<String>,
}

/// Visitor for tracking Python imports in AST.
///
/// `imports`: Maps top-level module names to their import locations.
///
/// `import_module_names`: Tracks import names (including aliases) that
/// refer to the `importlib.import_module` function itself, i.e. the import
/// alias for `importlib` package and/or the `importlib.import_module` function.
///
/// `typing_aliases`: Tracks aliases of the `typing` module, so we can
/// detect `if <alias>.TYPE_CHECKING` blocks.
impl ImportVisitor {
    pub fn new() -> Self {
        Self {
            imports: HashMap::new(),
            import_module_names: HashSet::new(),
            typing_aliases: HashSet::new(),
        }
    }

    pub fn get_imports(self) -> HashMap<String, Vec<TextRange>> {
        self.imports
    }

    /// Handles regular import statements (e.g., `import foo` or `import foo as bar`).
    ///
    /// Processes each name in the import statement (dealiasing if needed), and adds the
    /// top-level module to the `imports` map.
    ///
    /// Imports of the `importlib` package are handled as a special case: its name (or alias),
    /// suffixed with `.import_module`, is stored in `import_module_names`. This is done to
    /// indicate how we should look out for dynamic imports in the code that follows.
    fn handle_import(&mut self, import_stmt: &StmtImport) {
        for alias in &import_stmt.names {
            let top_level_module = get_top_level_module_name(alias.name.as_str());
            self.imports
                .entry(top_level_module)
                .or_default()
                .push(alias.range);

            if alias.name.as_str() == "importlib" {
                let name = alias
                    .asname
                    .as_ref()
                    .map_or("importlib", ruff_python_ast::Identifier::as_str);

                self.import_module_names
                    .insert(format!("{name}.import_module"));
            }

            if alias.name.as_str() == "typing" {
                let name = alias
                    .asname
                    .as_ref()
                    .map_or("typing", ruff_python_ast::Identifier::as_str);

                self.typing_aliases.insert(name.to_string());
            }
        }
    }

    /// Handles "from" import statements (e.g., `from foo import bar` or `from foo import bar as baz`).
    ///
    /// Processes the module which the names are being imported from, adds it to the `imports` map
    /// if it's a top-level import.
    ///
    /// Imports of `import_module` from the `importlib` package are handled as a special case: its
    /// name (or alias), prefixed with "importlib.", is stored in `import_module_names`. This is done to
    /// indicate how we should look out for dynamic imports in the code that follows.
    fn handle_import_from(&mut self, import_from_stmt: &StmtImportFrom) {
        if let Some(module) = &import_from_stmt.module
            && import_from_stmt.level == 0
        {
            let module_name = module.as_str();
            self.imports
                .entry(get_top_level_module_name(module_name))
                .or_default()
                .push(import_from_stmt.range);

            if module_name == "importlib" {
                for alias in &import_from_stmt.names {
                    if alias.name.as_str() == "import_module" {
                        let name = alias
                            .asname
                            .as_ref()
                            .map_or("import_module", ruff_python_ast::Identifier::as_str);
                        self.import_module_names.insert(name.to_string());
                    }
                }
            }

            if module_name == "typing" {
                self.typing_aliases.insert("typing".to_string());
            }
        }
    }

    /// Handles expression statements, looking for dynamic imports using `importlib.import_module`.
    ///
    /// This function checks if the expression is a call to a function that might be `importlib.import_module`
    /// (which could be import aliased at either the package or function name). If so, processes the imported
    /// module name (which must be given as a string literal, not a variable) and adds it to the `imports` map.
    fn handle_expr(&mut self, expr_stmt: &StmtExpr) {
        // Check for dynamic imports using `importlib.import_module`
        if let Expr::Call(call_expr) = expr_stmt.value.as_ref() {
            let is_import_module = match call_expr.func.as_ref() {
                Expr::Attribute(attr_expr) => {
                    if let Expr::Name(name) = attr_expr.value.as_ref() {
                        self.import_module_names
                            .contains(&format!("{}.import_module", name.id.as_str()))
                    } else {
                        false
                    }
                }
                Expr::Name(name) => self.import_module_names.contains(name.id.as_str()),
                _ => false,
            };

            if is_import_module
                && let Some(Expr::StringLiteral(string_literal)) = call_expr.arguments.args.first()
            {
                let top_level_module = get_top_level_module_name(&string_literal.value.to_string());
                self.imports
                    .entry(top_level_module)
                    .or_default()
                    .push(expr_stmt.range);
            }
        }
    }
}

impl<'a> Visitor<'a> for ImportVisitor {
    fn visit_stmt(&mut self, stmt: &'a Stmt) {
        match stmt {
            Stmt::Import(import_stmt) => self.handle_import(import_stmt),
            Stmt::ImportFrom(import_from_stmt) => self.handle_import_from(import_from_stmt),
            Stmt::Expr(expr_stmt) => self.handle_expr(expr_stmt),
            Stmt::If(if_stmt) if is_guarded_by_type_checking(if_stmt, &self.typing_aliases) => {
                // Avoid parsing imports that are only evaluated by type checkers.
            }
            _ => walk_stmt(self, stmt), // Delegate other statements to walk_stmt
        }
    }
}

/// Extracts the top-level module name from a potentially nested module path.
/// e.g. when a `module_name` is `foo.bar`, this returns `foo`.
fn get_top_level_module_name(module_name: &str) -> String {
    module_name
        .split('.')
        .next()
        .unwrap_or(module_name)
        .to_owned()
}

/// Checks if we are in a block guarded by `typing.TYPE_CHECKING` or an alias thereof.
fn is_guarded_by_type_checking(if_stmt: &StmtIf, typing_aliases: &HashSet<String>) -> bool {
    match &if_stmt.test.as_ref() {
        Expr::Attribute(ExprAttribute { value, attr, .. }) => {
            if let Expr::Name(ExprName { id, .. }) = value.as_ref()
                && typing_aliases.contains(id.as_str())
                && attr.as_str() == "TYPE_CHECKING"
            {
                return true;
            }
        }
        Expr::Name(ExprName { id, .. }) if id == "TYPE_CHECKING" => {
            return true;
        }
        _ => (),
    }

    false
}
