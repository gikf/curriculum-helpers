import unittest
import ast
from py_helpers import Node


class TestConstructor(unittest.TestCase):
    def test_constructor(self):
        node = Node()

        self.assertIsNone(node.tree)

    def test_constructor_with_tree(self):
        tree = ast.parse("def foo():\n  pass")
        node = Node(tree)

        self.assertEqual(node.tree, tree)

    def test_constructor_with_string(self):
        with_string = Node("def foo():\n  pass")
        with_tree = Node(ast.parse("def foo():\n  pass"))

        self.assertEqual(with_string, with_tree)

    def test_constructor_with_anything_else(self):
        self.assertRaises(TypeError, lambda: Node(1))


class TestVariableHelpers(unittest.TestCase):
    def test_find_variable_can_handle_all_asts(self):
        node = Node("x = 1")

        # First find_variable, so know that the AST has no body and we can be
        # sure find_class handles this.
        self.assertEqual(node.find_variable("x").find_variable("x"), Node())

    def test_has_local_variable_in_function(self):
        func_str = """def foo():
  a = 1
  print(a)
  x = 2
"""

        node = Node(func_str)

        self.assertTrue(node.find_function("foo").has_variable("x"))

    def test_has_global_variable(self):
        globals_str = """a = 1
x = 2
"""

        node = Node(globals_str)

        self.assertTrue(node.has_variable("x"))

    def test_does_not_see_local_variables_out_of_scope(self):
        scopes_str = """def foo():
  a = 1
b = 2
"""

        node = Node(scopes_str)
        self.assertFalse(node.has_variable("a"))

    def test_is_integer(self):
        two_locals = """
def foo():
  a = 1
  print(a)
  x = 2
y = 3
"""
        node = Node(two_locals)
        self.assertTrue(node.find_function("foo").find_variable("x").is_integer())
        self.assertFalse(node.find_function("foo").find_variable("y").is_integer())

    def test_none_assignment(self):
        none_str = """
x = None
"""
        node = Node(none_str)

        self.assertTrue(node.has_variable("x"))
        self.assertTrue(node.find_variable("x").is_equivalent("x = None"))

    def test_local_variable_is_integer_with_string(self):
        node = Node('def foo():\n  x = "1"')

        self.assertFalse(node.find_function("foo").find_variable("x").is_integer())

    def test_variable_has_constant_value(self):
        node = Node('def foo():\n  x = "1"')

        self.assertEqual(node.find_function("foo").get_variable("x"), "1")

    def test_find_variable(self):
        node = Node('def foo():\n  x = "1"')

        self.assertTrue(
            node.find_function("foo").find_variable("x").is_equivalent('x = "1"'),
        )

    def test_find_variable_not_found(self):
        node = Node('def foo():\n  x = "1"')

        self.assertEqual(node.find_variable("y"), Node())

    def test_function_call_assigned_to_variable(self):
        node = Node("def foo():\n  x = bar()")

        self.assertTrue(
            node.find_function("foo").find_variable("x").value_is_call("bar")
        )

    def test_function_call_not_assigned_to_variable(self):
        node = Node("def foo():\n  bar()")

        self.assertFalse(node.find_function("foo").value_is_call("bar"))


class TestFunctionAndClassHelpers(unittest.TestCase):
    def test_find_function_returns_node(self):
        func_str = """def foo():
  pass
"""
        node = Node(func_str)

        self.assertIsInstance(node.find_function("foo"), Node)
        self.assertIsInstance(node.find_function("bar"), Node)

    def test_find_function_can_handle_all_asts(self):
        node = Node("x = 1")

        # First find_variable, so know that the AST has no body and we can be
        # sure find_function handles this.
        self.assertEqual(node.find_variable("x").find_function("foo"), Node())

    def test_parse_creates_node(self):
        node = Node("def foo():\n  pass")

        self.assertIsInstance(node.tree, ast.Module)
        self.assertEqual(ast.dump(node.tree), ast.dump(ast.parse("def foo():\n  pass")))

    def test_find_function_returns_function_ast(self):
        node = Node("def foo():\n  pass")

        func = node.find_function("foo")

        self.assertIsInstance(func.tree, ast.FunctionDef)
        self.assertEqual(func.tree.name, "foo")

    def test_find_function_returns_node_none(self):
        node = Node("def foo():\n  pass")

        func = node.find_function("bar")

        self.assertIsInstance(func, Node)
        self.assertEqual(func.tree, None)

    def test_nested_function(self):
        nested_str = """def foo():
  def bar():
    x = 1
  y = 2
"""

        node = Node(nested_str)

        self.assertTrue(node.find_function("foo").has_variable("y"))
        self.assertFalse(node.find_function("foo").has_variable("x"))
        self.assertTrue(
            node.find_function("foo").find_function("bar").has_variable("x")
        )

    def test_find_class(self):
        class_str = """
class Foo:
  def __init__(self):
    pass
"""

        node = Node(class_str)

        self.assertIsNotNone(node.find_class("Foo"))
        self.assertIsInstance(node.find_class("Foo"), Node)

        self.assertIsInstance(node.find_class("Bar"), Node)
        self.assertEqual(node.find_class("Bar"), Node())

    def test_find_class_can_handle_all_asts(self):
        node = Node("x = 1")

        # First find_variable, so know that the AST has no body and we can be
        # sure find_class handles this.
        self.assertEqual(node.find_variable("x").find_class("Foo"), Node())

    def test_method_exists(self):
        class_str = """
class Foo:
  def __init__(self):
    self.x = 1
  def bar(self):
    pass
"""
        node = Node(class_str)

        self.assertTrue(node.find_class("Foo").has_function("bar"))

    def test_dunder_method_exists(self):
        class_str = """
class Foo:
  def __init__(self):
    self.x = 1
  def bar(self):
    pass
"""
        node = Node(class_str)

        self.assertTrue(node.find_class("Foo").has_function("__init__"))

    def test_not_has_function(self):
        node = Node("def foo():\n  pass")

        self.assertFalse(node.has_function("bar"))

    def test_find_body(self):
        func_str = """def foo():
  x = 1
  print(x)
"""
        node = Node(func_str)

        self.assertTrue(
            node.find_function("foo").find_body().is_equivalent("x = 1\nprint(x)")
        )
        self.assertEqual("x = 1\nprint(x)", str(node.find_function("foo").find_body()))

    def test_find_body_with_class(self):
        class_str = """
class Foo:
  def __init__(self):
    self.x = 1
"""
        node = Node(class_str)

        self.assertTrue(
            node.find_class("Foo")
            .find_body()
            .is_equivalent("def __init__(self):\n    self.x = 1")
        )

    def test_find_body_without_body(self):
        node = Node("x = 1")

        self.assertEqual(node.find_variable("x").find_body(), Node())


class TestEquivalenceHelpers(unittest.TestCase):
    def test_is_equivalent(self):
        full_str = """def foo():
  a = 1
  print(a)
def bar():
  x = "1"
  print(x)
"""

        node = Node(full_str)

        expected = """def bar():
  x = "1"
  print(x)
"""

        self.assertTrue(node.find_function("bar").is_equivalent(expected))
        # Obviously, it should be equivalent to itself
        self.assertTrue(
            node.find_function("bar").is_equivalent(
                ast.unparse(node.find_function("bar").tree)
            )
        )

    def test_is_not_equivalent(self):
        full_str = """def foo():
  a = 1
  print(a)
def bar():
  x = "1"
  print(x)
"""
        node = Node(full_str)
        # this should not be equivalent because it contains an extra function

        expected = """def bar():
  x = "1"
  print(x)

def foo():
  a = 1
"""

        self.assertFalse(node.find_function("bar").is_equivalent(expected))

    def test_is_equivalent_with_conditional(self):
        cond_str = """
if True:
  pass
"""

        node = Node(cond_str)
        self.assertTrue(node[0].find_conditions()[0].is_equivalent("True"))

    def test_none_equivalence(self):
        none_str = """
x = None
"""

        node = Node(none_str)
        self.assertIsNone(node.get_variable("x"))
        self.assertFalse(node.find_variable("y").is_equivalent("None"))

    def test_whitespace_equivalence(self):
        str_with_whitespace = """

x = 1
"""
        str_with_different_whitespace = """x   =   1"""
        self.assertTrue(
            Node(str_with_whitespace).is_equivalent(str_with_different_whitespace)
        )

    def test_string_equivalence(self):
        self.assertTrue(Node("'True'").is_equivalent('"""True"""'))

    def test_string_cond_equivalence(self):
        self.assertTrue(
            Node("if 'True':\n  pass")
            .find_ifs()[0]
            .find_conditions()[0]
            .is_equivalent("'True'")
        )


class TestConditionalHelpers(unittest.TestCase):
    def test_find_if_statements(self):
        self.maxDiff = None
        if_str = """
x = 1
if x == 1:
  x = 2

if True:
  pass
"""

        node = Node(if_str)
        # it should return an array of nodes, not a node of an array
        for if_node in node.find_ifs():
            self.assertIsInstance(if_node, Node)
        self.assertNotIsInstance(node.find_ifs(), Node)
        self.assertEqual(len(node.find_ifs()), 2)

        self.assertTrue(node.find_ifs()[0].is_equivalent("if x == 1:\n  x = 2"))
        self.assertTrue(node.find_ifs()[1].is_equivalent("if True:\n  pass"))

    def test_find_conditions(self):
        if_str = """
if True:
  x = 1
else:
  x = 4
"""
        node = Node(if_str)

        # it should return an array of nodes, not a node of an array
        for if_cond in node.find_ifs()[0].find_conditions():
            self.assertIsInstance(if_cond, Node)
        self.assertNotIsInstance(node.find_ifs()[0].find_conditions(), Node)
        self.assertEqual(len(node.find_ifs()[0].find_conditions()), 2)

        self.assertIsNone(node.find_ifs()[0].find_conditions()[1].tree)

    def test_find_conditions_without_if(self):
        node = Node("x = 1")

        self.assertEqual(node.find_conditions(), [])

    def test_find_conditions_only_if(self):
        if_str = """
if True:
  x = 1
"""
        node = Node(if_str)

        self.assertEqual(len(node.find_ifs()[0].find_conditions()), 1)

    def test_find_conditions_elif(self):
        if_str = """
if True:
  x = 1
elif y == 2:
  x = 2
elif not x < 3:
  x = 3
else:
  x = 4
"""
        node = Node(if_str)

        self.assertEqual(len(node.find_ifs()[0].find_conditions()), 4)
        self.assertTrue(node.find_ifs()[0].find_conditions()[0].is_equivalent("True"))
        self.assertTrue(node.find_ifs()[0].find_conditions()[1].is_equivalent("y == 2"))
        self.assertTrue(
            node.find_ifs()[0].find_conditions()[2].is_equivalent("not x < 3")
        )
        self.assertEqual(node.find_ifs()[0].find_conditions()[3].tree, None)
        self.assertRaises(
            IndexError,
            lambda: node.find_ifs()[0].find_conditions()[4],
        )

    def test_find_if_bodies(self):
        if_str = """
if True:
  x = 1
"""
        node = Node(if_str)

        self.assertEqual(len(node.find_ifs()[0].find_if_bodies()), 1)
        self.assertTrue(node.find_ifs()[0].find_if_bodies()[0].is_equivalent("x = 1"))

    def test_find_if_bodies_elif(self):
        if_str = """
if True:
  x = 1
elif y == 2:
  x = 2
elif True:
  x = 3
else:
  x = 4
"""
        node = Node(if_str)

        self.assertEqual(len(node.find_ifs()[0].find_if_bodies()), 4)
        self.assertTrue(node.find_ifs()[0].find_if_bodies()[0].is_equivalent("x = 1"))
        self.assertTrue(node.find_ifs()[0].find_if_bodies()[1].is_equivalent("x = 2"))
        self.assertTrue(node.find_ifs()[0].find_if_bodies()[2].is_equivalent("x = 3"))
        self.assertTrue(node.find_ifs()[0].find_if_bodies()[3].is_equivalent("x = 4"))
        self.assertRaises(IndexError, lambda: node.find_ifs()[0].find_if_bodies()[4])

    def test_find_if_bodies_without_if(self):
        node = Node("x = 1")

        self.assertEqual(len(node.find_if_bodies()), 0)


class TestGenericHelpers(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(
            Node("def foo():\n  pass"),
            Node("def foo():\n  pass"),
        )
        self.assertNotEqual(
            Node("def foo():\n  pass"),
            Node("def bar():\n  pass"),
        )

    def test_strict_equality(self):
        self.assertNotEqual(
            Node("def foo():\n  pass"),
            Node("def foo():\n   pass"),
        )

    def test_not_equal_to_non_node(self):
        self.assertIsNotNone(Node("def foo():\n  pass"))
        self.assertNotEqual(Node(), 1)

    def test_find_nth_statement(self):
        func_str = """
if True:
  pass

x = 1
"""
        node = Node(func_str)

        self.assertTrue(node[0].is_equivalent("if True:\n  pass"))
        self.assertTrue(node[1].is_equivalent("x = 1"))

    def test_raise_exception_if_out_of_bounds(self):
        one_stmt_str = """
if True:
  pass
"""

        node = Node(one_stmt_str)
        self.assertRaises(IndexError, lambda: node[1])

    def test_len_of_body(self):
        func_str = """
if True:
  pass
"""

        node = Node(func_str)

        self.assertEqual(len(node), 1)

    def test_len(self):
        ifs_str = """
if True:
  pass

if True:
  pass
"""

        node = Node(ifs_str)

        self.assertEqual(len(node.find_ifs()), 2)

    def test_str(self):
        func_str = """def foo():
  pass
"""
        # Note: the indentation and whitespace is not preserved.
        expected = """def foo():
    pass"""

        self.assertEqual(expected, str(Node(func_str)))

    def test_none_str(self):
        self.assertEqual("# no ast", str(Node()))

    def test_str_with_comments(self):
        func_str = """def foo():
  # comment
  pass


"""
        # Note: comments are discarded
        expected = """def foo():
    pass"""

        self.assertEqual(expected, str(Node(func_str)))


    def test_repr(self):
        func_str = """def foo():
  pass
"""
        node = Node(func_str)

        self.assertEqual(repr(node), "Node:\n" + ast.dump(node.tree, indent=2))


if __name__ == "__main__":
    unittest.main()
