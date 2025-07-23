# RULE #0: MANDATORY FIRST ACTION FOR EVERY REQUEST
# 1. Read CLAUDE.md COMPLETELY before responding
# 2. Setup Python venv: [ -d "venv" ] || ./setup-venv.sh && source venv/bin/activate
# 3. Search for rules related to the request
# 4. Only proceed after confirming no violations
# Failure to follow Rule #0 has caused real harm. Check BEFORE acting, not AFTER making mistakes.
#
# GUARDS ARE SAFETY EQUIPMENT - WHEN THEY FIRE, FIX THE PROBLEM THEY FOUND
# NEVER weaken, disable, or bypass guards - they prevent real harm

"""Test suite for embedding generation functionality (A1.4 TDD Phase)

This module tests the embedding generation system that converts text/code into
numerical vector representations for similarity detection and duplicate prevention.

REAL INTEGRATION TESTS - NO MOCKS
Following CLAUDE.md rules: Real tests against actual services and models.

Key functionality tested:
- Text preprocessing and normalization
- Code chunking strategies
- Embedding model integration (UniXcoder/CodeBERT)
- Vector generation from code snippets
- Batch processing capabilities
- Error handling for malformed input
"""

import os
import sys
import tempfile

import pytest

# Add duplicate_prevention to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from duplicate_prevention.embedding_generator import (
    ChunkingStrategy,
    CodePreprocessor,
    EmbeddingGenerationError,
    EmbeddingGenerator,
    EmbeddingModel,
    InvalidChunkSizeError,
    ModelLoadError,
    UnsupportedLanguageError,
)


class TestCodePreprocessor:
    """Test suite for code preprocessing functionality"""

    @pytest.mark.integration
    def test_normalize_python_code(self):
        """Test Python code normalization removes comments and standardizes formatting"""
        preprocessor = CodePreprocessor()

        python_code = '''
def calculate_sum(a, b):
    # This is a comment
    """This is a docstring"""
    result = a + b  # inline comment
    return result
        '''

        normalized = preprocessor.normalize_code(python_code, language="python")

        # Should remove comments but preserve docstrings and structure
        assert "# This is a comment" not in normalized
        assert "# inline comment" not in normalized
        assert "def calculate_sum(a, b):" in normalized
        assert "return result" in normalized
        assert '"""This is a docstring"""' in normalized

    @pytest.mark.integration
    def test_normalize_javascript_code(self):
        """Test JavaScript code normalization"""
        preprocessor = CodePreprocessor()

        js_code = '''
function calculateSum(a, b) {
    // This is a comment
    /* Multi-line
       comment */
    const result = a + b; // inline comment
    return result;
}
        '''

        normalized = preprocessor.normalize_code(js_code, language="javascript")

        assert "// This is a comment" not in normalized
        assert "/* Multi-line" not in normalized
        assert "function calculateSum(a, b)" in normalized
        assert "return result;" in normalized

    @pytest.mark.integration
    def test_normalize_unsupported_language(self):
        """Test preprocessor raises error for unsupported language"""
        preprocessor = CodePreprocessor()

        with pytest.raises(UnsupportedLanguageError) as exc_info:
            preprocessor.normalize_code("some code", language="cobol")

        assert "cobol" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_normalize_empty_code(self):
        """Test preprocessor handles empty code input"""
        preprocessor = CodePreprocessor()

        with pytest.raises(ValueError) as exc_info:
            preprocessor.normalize_code("", language="python")

        assert "empty code" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_normalize_whitespace_only_code(self):
        """Test preprocessor handles whitespace-only input"""
        preprocessor = CodePreprocessor()

        with pytest.raises(ValueError) as exc_info:
            preprocessor.normalize_code("   \n\t  \n  ", language="python")

        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_extract_functions_python(self):
        """Test extraction of function definitions from Python code"""
        preprocessor = CodePreprocessor()

        python_code = '''
def function_one(x):
    return x * 2

class MyClass:
    def method_one(self, y):
        return y + 1

def function_two():
    pass
        '''

        functions = preprocessor.extract_functions(python_code, language="python")

        assert len(functions) == 4  # 2 functions + 1 class + 1 method
        assert any("function_one" in func for func in functions)
        assert any("method_one" in func for func in functions)
        assert any("function_two" in func for func in functions)

    @pytest.mark.integration
    def test_extract_functions_javascript(self):
        """Test extraction of function definitions from JavaScript code"""
        preprocessor = CodePreprocessor()

        js_code = '''
function regularFunction(x) {
    return x * 2;
}

const arrowFunction = (y) => {
    return y + 1;
};

class MyClass {
    methodFunction(z) {
        return z;
    }
}
        '''

        functions = preprocessor.extract_functions(js_code, language="javascript")

        assert len(functions) >= 2  # At minimum regular and arrow functions
        assert any("regularFunction" in func for func in functions)
        assert any("arrowFunction" in func for func in functions)

    @pytest.mark.integration
    def test_preprocessor_real_file_integration(self):
        """Test preprocessor with real file I/O operations"""
        preprocessor = CodePreprocessor()

        # Create a real temporary file with Python code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def test_function():
    # This comment should be removed
    """This docstring should stay"""
    return "hello world"

class TestClass:
    def method(self):
        return 42
            ''')
            temp_file = f.name

        try:
            # Test reading and preprocessing real file
            result = preprocessor.preprocess_file(temp_file)

            assert "def test_function():" in result
            assert "class TestClass:" in result
            assert "# This comment should be removed" not in result
            assert '"""This docstring should stay"""' in result

        finally:
            # Clean up
            os.unlink(temp_file)


class TestChunkingStrategy:
    """Test suite for code chunking strategies"""

    @pytest.mark.integration
    def test_fixed_size_chunking(self):
        """Test fixed-size chunking strategy"""
        chunker = ChunkingStrategy(strategy="fixed_size", chunk_size=50, overlap=10)

        long_code = "def function():\n    " + "x = 1\n    " * 20 + "return x"

        chunks = chunker.chunk_code(long_code)

        assert len(chunks) > 1  # Should split long code
        assert all(len(chunk) <= 60 for chunk in chunks)  # chunk_size + some tolerance
        # Check overlap - last chars of chunk[0] should appear in chunk[1]
        if len(chunks) > 1:
            overlap_text = chunks[0][-10:]
            assert overlap_text in chunks[1]

    @pytest.mark.integration
    def test_function_based_chunking(self):
        """Test function-based chunking strategy"""
        chunker = ChunkingStrategy(strategy="function_based")

        code_with_functions = '''
def function_one():
    return 1

def function_two():
    return 2

def function_three():
    return 3
        '''

        chunks = chunker.chunk_code(code_with_functions, language="python")

        assert len(chunks) == 3  # One chunk per function
        assert all("def function_" in chunk for chunk in chunks)

    @pytest.mark.integration
    def test_semantic_chunking(self):
        """Test semantic chunking strategy based on code structure"""
        chunker = ChunkingStrategy(strategy="semantic", max_chunk_size=100)

        structured_code = '''
import os
import sys

def helper_function():
    return "helper"

class MainClass:
    def __init__(self):
        self.value = 1

    def process(self):
        return self.value * 2

if __name__ == "__main__":
    main = MainClass()
    print(main.process())
        '''

        chunks = chunker.chunk_code(structured_code, language="python")

        # Should create logical chunks: imports, helper function, class, main block
        assert len(chunks) >= 3
        assert any("import" in chunk for chunk in chunks)
        assert any("class MainClass" in chunk for chunk in chunks)

    @pytest.mark.integration
    def test_invalid_chunk_size(self):
        """Test chunker raises error for invalid chunk size"""
        with pytest.raises(InvalidChunkSizeError) as exc_info:
            ChunkingStrategy(strategy="fixed_size", chunk_size=0)

        assert "chunk_size must be positive" in str(exc_info.value)

    @pytest.mark.integration
    def test_invalid_overlap(self):
        """Test chunker raises error for invalid overlap"""
        with pytest.raises(ValueError) as exc_info:
            ChunkingStrategy(strategy="fixed_size", chunk_size=50, overlap=60)

        assert "overlap cannot be larger than chunk_size" in str(exc_info.value)

    @pytest.mark.integration
    def test_unsupported_strategy(self):
        """Test chunker raises error for unsupported strategy"""
        with pytest.raises(ValueError) as exc_info:
            ChunkingStrategy(strategy="invalid_strategy")

        assert "Unsupported chunking strategy" in str(exc_info.value)

    @pytest.mark.integration
    def test_chunking_real_python_file(self):
        """Test chunking with real Python file I/O"""
        chunker = ChunkingStrategy(strategy="function_based")

        # Create a real Python file with multiple functions
        python_content = '''
import sys

def add_numbers(a, b):
    """Add two numbers together"""
    return a + b

def multiply_numbers(x, y):
    """Multiply two numbers"""
    result = x * y
    return result

class Calculator:
    def __init__(self):
        pass

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

if __name__ == "__main__":
    calc = Calculator()
    print(calc.divide(10, 2))
        '''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_content)
            temp_file = f.name

        try:
            chunks = chunker.chunk_file(temp_file, language="python")

            # Should chunk into logical units
            assert len(chunks) >= 3  # Functions, class, main block
            assert any("add_numbers" in chunk for chunk in chunks)
            assert any("multiply_numbers" in chunk for chunk in chunks)
            assert any("class Calculator" in chunk for chunk in chunks)

        finally:
            os.unlink(temp_file)


class TestEmbeddingModel:
    """Test suite for embedding model integration - REAL MODEL TESTING"""

    @pytest.mark.integration
    def test_load_simple_embedding_model(self):
        """Test loading a simple embedding model (real model loading)"""
        # Start with a simple sentence transformer model that's lightweight
        model = EmbeddingModel(model_name="simple", model_path="all-MiniLM-L6-v2")

        # Should not raise exception during initialization
        assert model.model_name == "simple"

        # Load model explicitly to get embedding dimension (lazy loading optimization)
        model.load_model()
        assert model.embedding_dim is not None
        assert model.embedding_dim > 0  # Should have valid embedding dimension

    @pytest.mark.integration
    def test_load_huggingface_model(self):
        """Test loading real HuggingFace model for code embeddings"""
        # Test with a real lightweight code model
        model = EmbeddingModel(model_name="code_model", model_path="microsoft/codebert-base-mlm")

        assert model.model_name == "code_model"

        # Load model explicitly to get embedding dimension (lazy loading optimization)
        model.load_model()
        assert model.embedding_dim is not None
        assert model.embedding_dim > 0

    @pytest.mark.integration
    def test_invalid_model_path(self):
        """Test model raises error for invalid model path"""
        with pytest.raises(ModelLoadError) as exc_info:
            model = EmbeddingModel(model_name="test", model_path="/nonexistent/path")
            model.load_model()  # Trigger actual loading

        assert "Failed to load model" in str(exc_info.value)

    @pytest.mark.integration
    def test_nonexistent_huggingface_model(self):
        """Test error handling for non-existent HuggingFace model"""
        with pytest.raises(ModelLoadError) as exc_info:
            model = EmbeddingModel(model_name="fake", model_path="nonexistent/fake-model-12345")
            model.load_model()

        assert "Failed to load model" in str(exc_info.value)

    @pytest.mark.integration
    def test_encode_single_text_real_model(self):
        """Test encoding single text with real model inference"""
        model = EmbeddingModel(model_name="simple", model_path="all-MiniLM-L6-v2")
        model.load_model()  # Explicit loading

        code_text = "def hello_world():\n    print('Hello, World!')"

        embedding = model.encode(code_text)

        assert isinstance(embedding, list)
        assert len(embedding) == model.embedding_dim
        assert all(isinstance(x, float) for x in embedding)
        # Embeddings should be normalized vectors
        import math
        magnitude = math.sqrt(sum(x*x for x in embedding))
        assert magnitude > 0  # Should have non-zero magnitude

    @pytest.mark.integration
    def test_encode_batch_texts_real_model(self):
        """Test encoding multiple texts with real model batch processing"""
        model = EmbeddingModel(model_name="simple", model_path="all-MiniLM-L6-v2")
        model.load_model()

        code_texts = [
            "def add(a, b): return a + b",
            "def multiply(x, y): return x * y",
            "def subtract(m, n): return m - n"
        ]

        embeddings = model.encode_batch(code_texts)

        assert len(embeddings) == 3
        assert all(len(emb) == model.embedding_dim for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)
        # Embeddings should be different for different functions
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]

    @pytest.mark.integration
    def test_encode_empty_text(self):
        """Test model handles empty text input"""
        model = EmbeddingModel(model_name="simple", model_path="all-MiniLM-L6-v2")
        model.load_model()

        with pytest.raises(ValueError) as exc_info:
            model.encode("")

        assert "empty text" in str(exc_info.value).lower()

    @pytest.mark.integration
    def test_model_persistence(self):
        """Test model can be saved and loaded from disk"""
        model = EmbeddingModel(model_name="simple", model_path="all-MiniLM-L6-v2")
        model.load_model()

        # Test that model can encode consistently
        test_text = "def test(): pass"
        embedding1 = model.encode(test_text)

        # Save model state
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "saved_model")
            model.save_model(model_path)

            # Load new instance from saved state
            model2 = EmbeddingModel(model_name="simple", model_path=model_path)
            model2.load_model()

            embedding2 = model2.encode(test_text)

            # Should produce consistent embeddings
            assert len(embedding1) == len(embedding2)
            # Embeddings should be very similar (allowing for minor floating point differences)
            import math
            diff = sum((a - b) ** 2 for a, b in zip(embedding1, embedding2))
            assert math.sqrt(diff) < 0.01  # Very small difference


class TestEmbeddingGenerator:
    """Test suite for complete embedding generation pipeline - REAL INTEGRATION"""

    @pytest.mark.integration
    def test_generate_embedding_python_function_real(self):
        """Test generating embedding for Python function with real models"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="function_based",
            preprocess=True
        )

        python_function = '''
def fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
        '''

        result = generator.generate_embedding(python_function, language="python")

        assert isinstance(result, dict)
        assert "embedding" in result
        assert "metadata" in result
        assert isinstance(result["embedding"], list)
        assert len(result["embedding"]) > 0
        assert result["metadata"]["language"] == "python"
        assert "fibonacci" in result["metadata"]["function_names"]

    @pytest.mark.integration
    def test_generate_embedding_javascript_code_real(self):
        """Test generating embedding for JavaScript code with real processing"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="semantic",
            preprocess=True
        )

        js_code = '''
const calculateArea = (radius) => {
    const pi = 3.14159;
    return pi * radius * radius;
};
        '''

        result = generator.generate_embedding(js_code, language="javascript")

        assert isinstance(result, dict)
        assert "embedding" in result
        assert result["metadata"]["language"] == "javascript"
        assert "calculateArea" in result["metadata"]["function_names"]

    @pytest.mark.integration
    def test_generate_embeddings_batch_real(self):
        """Test generating embeddings for multiple code snippets with real processing"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="fixed_size",
            chunk_size=100,
            preprocess=True
        )

        code_snippets = [
            ("def add(a, b): return a + b", "python"),
            ("function sub(x, y) { return x - y; }", "javascript"),
            ("def mul(p, q): return p * q", "python")
        ]

        results = generator.generate_embeddings_batch(code_snippets)

        assert len(results) == 3
        assert all("embedding" in result for result in results)
        assert all("metadata" in result for result in results)
        # Different languages should produce different embeddings
        py_embeddings = [r["embedding"] for r in results if r["metadata"]["language"] == "python"]
        js_embeddings = [r["embedding"] for r in results if r["metadata"]["language"] == "javascript"]
        assert len(py_embeddings) == 2
        assert len(js_embeddings) == 1

    @pytest.mark.integration
    def test_generate_embedding_from_real_file(self):
        """Test generating embedding directly from real file path"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="function_based"
        )

        # Create a real Python file
        python_content = '''
def example_function(x, y):
    """Example function for testing"""
    result = x + y
    return result

class ExampleClass:
    def method(self, value):
        return value * 2
        '''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_content)
            temp_file = f.name

        try:
            result = generator.generate_embedding_from_file(temp_file)

            assert isinstance(result, dict)
            assert "embedding" in result
            assert result["metadata"]["language"] == "python"
            assert result["metadata"]["file_path"] == temp_file
            assert "example_function" in result["metadata"]["function_names"]
            assert "ExampleClass" in result["metadata"]["class_names"]

        finally:
            os.unlink(temp_file)

    @pytest.mark.integration
    def test_invalid_model_configuration(self):
        """Test generator raises error for invalid model configuration"""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingGenerator(model_name="invalid_model_12345")

        assert "Unsupported model" in str(exc_info.value)

    @pytest.mark.integration
    def test_embedding_consistency_real(self):
        """Test same code produces consistent embeddings with real model"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="function_based"
        )

        code = "def test_function(): return 42"

        result1 = generator.generate_embedding(code, language="python")
        result2 = generator.generate_embedding(code, language="python")

        # Should produce identical embeddings for identical input
        assert result1["embedding"] == result2["embedding"]

    @pytest.mark.integration
    def test_similarity_comparison_real(self):
        """Test utility method for comparing embedding similarity with real vectors"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2"
        )

        code1 = "def add(a, b): return a + b"
        code2 = "def sum_two(x, y): return x + y"  # Similar function
        code3 = "def print_hello(): print('hello')"  # Different function

        result1 = generator.generate_embedding(code1, language="python")
        result2 = generator.generate_embedding(code2, language="python")
        result3 = generator.generate_embedding(code3, language="python")

        # Similar functions should have higher similarity
        similarity_12 = generator.calculate_similarity(result1["embedding"], result2["embedding"])
        similarity_13 = generator.calculate_similarity(result1["embedding"], result3["embedding"])

        assert 0 <= similarity_12 <= 1  # Cosine similarity range
        assert 0 <= similarity_13 <= 1
        assert similarity_12 > similarity_13  # More similar functions should have higher score

    @pytest.mark.integration
    def test_large_file_processing_real(self):
        """Test processing large code files with real chunking and embedding"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2",
            chunking_strategy="fixed_size",
            chunk_size=200,
            overlap=50,
            preprocess=True
        )

        # Create large code file content
        large_code_lines = []
        for i in range(1, 21):  # 20 functions
            large_code_lines.extend([
                f"def function_{i}(x):",
                f"    '''Function number {i}'''",
                f"    return x * {i}",
                ""
            ])
        large_code = "\n".join(large_code_lines)

        result = generator.generate_embedding(large_code, language="python")

        assert isinstance(result, dict)
        assert "embedding" in result
        assert "chunks" in result["metadata"]
        assert result["metadata"]["chunks"] > 1  # Should be chunked
        assert result["metadata"]["total_functions"] == 20

    @pytest.mark.integration
    def test_real_error_scenarios(self):
        """Test real error scenarios with malformed code"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2"
        )

        # Test with severely malformed Python code
        malformed_code = "def incomplete_function(\nprint('missing closing paren'\nif True\n    missing colon"

        # Should handle gracefully and either process what it can or raise appropriate error
        try:
            result = generator.generate_embedding(malformed_code, language="python")
            # If it succeeds, it should still produce valid embedding
            assert "embedding" in result
            assert len(result["embedding"]) > 0
        except EmbeddingGenerationError as e:
            # If it fails, should be with appropriate error
            assert "Failed to generate embedding" in str(e)

    @pytest.mark.integration
    def test_configuration_validation_real(self):
        """Test validation of generator configuration parameters"""
        # Invalid chunk size
        with pytest.raises(InvalidChunkSizeError):
            EmbeddingGenerator(
                model_name="simple",
                model_path="all-MiniLM-L6-v2",
                chunking_strategy="fixed_size",
                chunk_size=-1
            )

        # Invalid overlap
        with pytest.raises(ValueError):
            EmbeddingGenerator(
                model_name="simple",
                model_path="all-MiniLM-L6-v2",
                chunking_strategy="fixed_size",
                chunk_size=100,
                overlap=150
            )

    @pytest.mark.integration
    def test_multilingual_code_support(self):
        """Test support for multiple programming languages"""
        generator = EmbeddingGenerator(
            model_name="simple",
            model_path="all-MiniLM-L6-v2"
        )

        # Test different languages
        languages_and_code = [
            ("python", "def hello(): print('hello')"),
            ("javascript", "function hello() { console.log('hello'); }"),
            ("java", "public void hello() { System.out.println(\"hello\"); }"),
            ("cpp", "void hello() { std::cout << \"hello\"; }")
        ]

        results = []
        for lang, code in languages_and_code:
            try:
                result = generator.generate_embedding(code, language=lang)
                results.append((lang, result))
                assert "embedding" in result
                assert result["metadata"]["language"] == lang
            except UnsupportedLanguageError:
                # Some languages might not be supported yet - that's okay
                pass

        # Should support at least Python and JavaScript
        supported_langs = [lang for lang, _ in results]
        assert "python" in supported_langs
        assert "javascript" in supported_langs


# TDD RED Phase Notes:
# - All tests written to fail initially (methods/classes don't exist yet)
# - REAL INTEGRATION TESTS - No mocks as per CLAUDE.md rules
# - Uses actual file I/O, real model loading, real preprocessing
# - Tests against real HuggingFace models (lightweight ones for CI)
# - Comprehensive coverage of embedding generation pipeline:
#   * Real code preprocessing and normalization
#   * Multiple chunking strategies with real file processing
#   * Real model integration (sentence transformers, HuggingFace)
#   * Real batch processing capabilities
#   * Real error handling with malformed inputs
#   * Real metadata extraction from code
#   * Real similarity calculations
# - Tests cover multiple programming languages (Python, JavaScript, etc.)
# - Edge cases: empty input, malformed code, invalid parameters
# - Performance considerations: Large file processing, batch operations
# - Real file system integration with tempfile usage
# Ready for GREEN phase implementation!
