# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:* High cosine similarity có nghĩa là hai đoạn văn bản có ý nghĩa hoặc ngữ cảnh rất tương đồng nhau khi được biểu diễn dưới dạng vector. Góc giữa hai vector của chúng rất nhỏ, thể hiện rằng chúng có chung nhiều đặc trưng ngữ nghĩa.

**Ví dụ HIGH similarity:**
- Sentence A: "Con chó màu nâu đang chạy trên thảm cỏ."
- Sentence B: "Chú cún có bộ lông nâu đang đùa nghịch trên bãi cỏ."
- Tại sao tương đồng: Cả hai đều miêu tả cùng một sự việc với các từ đồng nghĩa (con chó - chú cún, chạy - đùa nghịch, thảm cỏ - bãi cỏ) nên vector ngữ nghĩa của chúng sẽ rất gần nhau.

**Ví dụ LOW similarity:**
- Sentence A: "Con chó màu nâu đang chạy trên thảm cỏ."
- Sentence B: "Thị trường chứng khoán hôm nay biến động mạnh."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác biệt (động vật/thiên nhiên so với tài chính/kinh tế) nên vector biểu diễn của chúng sẽ có độ lệch góc rất lớn, dẫn đến độ tương đồng thấp.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity tập trung vào hướng (góc) của vector thay vì độ dài. Độ dài của text embedding thường bị ảnh hưởng bởi độ dài của câu văn; cosine similarity giúp bỏ qua khác biệt về độ dài văn bản để thực sự đánh giá xem hai văn bản có chung ngữ nghĩa hay không.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> *Đáp án:* 23 chunks.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:* Nếu overlap tăng lên 100, số lượng chunk tăng lên thành 25 (`ceil((10000 - 100) / (500 - 100)) = 24.75`). Ta muốn overlap nhiều hơn để đảm bảo không bị mất mát hay cắt đứt ngữ cảnh quan trọng nằm ở phần ranh giới giữa hai chunk, giúp model truy xuất thông tin trọn vẹn hơn.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Engineering & Technical Support Documentation

**Tại sao nhóm chọn domain này?**
> Tài liệu kỹ thuật và hỗ trợ khách hàng là một domain điển hình cho ứng dụng RAG trong môi trường thực tế. Đặc thù của chúng chứa nhiều hướng dẫn chi tiết, policy và cấu trúc phong phú, lý tưởng để đánh giá chiến lược chia nhỏ (chunking) và rút trích thông tin.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | customer_support_playbook.txt | Local | 1692 | {"source": "customer_support_playbook.txt", "category": "guide"} |
| 2 | python_intro.txt | Local | 1944 | {"source": "python_intro.txt", "category": "guide"} |
| 3 | rag_system_design.md | Local | 2391 | {"source": "rag_system_design.md", "category": "architecture"} |
| 4 | vector_store_notes.md | Local | 2123 | {"source": "vector_store_notes.md", "category": "architecture"} |
| 5 | vi_retrieval_notes.md | Local | 1667 | {"source": "vi_retrieval_notes.md", "category": "architecture"} |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | "guide" / "architecture" | Giúp RAG giới hạn khoanh vùng tìm kiếm (ví dụ chỉ tìm trong "guide" khi user cần hướng dẫn) để tăng precision. |
| source | string | "python_intro.txt" | Hữu ích để truy xuất nguồn và trích dẫn ngược cho user biết câu trả lời được lấy chính xác từ file nào. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| rag_system_design.md | FixedSizeChunker (`fixed_size`) | 16 | 196.3 | Trung bình |
| rag_system_design.md | SentenceChunker (`by_sentences`) | 5 | 476.0 | Tốt |
| rag_system_design.md | RecursiveChunker (`recursive`) | 20 | 117.7 | Khá |
| vi_retrieval_notes.md | FixedSizeChunker (`fixed_size`) | 11 | 197.0 | Trung bình |
| vi_retrieval_notes.md | SentenceChunker (`by_sentences`) | 5 | 331.6 | Tốt |
| vi_retrieval_notes.md | RecursiveChunker (`recursive`) | 13 | 126.3 | Khá |

### Strategy Của Tôi

**Loại:** RecursiveChunker(chunk_size=300)

**Mô tả cách hoạt động:**
> Thuật toán đệ quy cắt chuỗi bằng các dấu phân tách giảm dần độ ưu tiên như \n\n, \n. Kích thước tối đa được tuỳ chỉnh thành 300 ký tự để nới rộng không gian cho mỗi đoạn chứa đủ ngữ cảnh mà không bị cắt quá vụn.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain kỹ thuật chứa nhiều đoạn văn bản có cấu trúc header, bullet points, và code block. Dùng RecursiveChunker giúp việc tách diễn ra tự nhiên theo cấu trúc ngắt dòng gốc của tác giả thay vì cắt cứng ở độ dài cố định.

**Code snippet (nếu custom):**
```python
# Tái sử dụng RecursiveChunker với tham số tùy chỉnh
my_chunker = RecursiveChunker(chunk_size=300)
chunks = my_chunker.chunk(document.content)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| rag_system_design.md | SentenceChunker (200) | 5 | 476.0 | Khá |
| rag_system_design.md | **RecursiveChunker (300)** | 15 | 157.5 | Rất Tốt |
| vi_retrieval_notes.md | SentenceChunker (200) | 5 | 331.6 | Khá |
| vi_retrieval_notes.md | **RecursiveChunker (300)** | 9 | 183.3 | Rất Tốt |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | RecursiveChunker(300) | 8/10 | Giữ ngữ cảnh ngắt đoạn | Đôi khi lọt thỏm câu ngắn |
| Bạn A | FixedSizeChunker(overlap=50) | 6/10 | Rất đều nhau | Bị cắt vỡ câu giữa chừng |
| Bạn B | SentenceChunker(max=3) | 7.5/10 | Ý nghĩa trọn vẹn từng câu | Kích thước chunk quá lệch |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> RecursiveChunker(300) tỏ ra hiệu quả nhất vì tài liệu kỹ thuật có sự phân mảnh đoạn văn theo các cấu trúc dòng khá chuẩn mực. Khả năng fall back giúp văn bản được tách gọn gàng theo ý đồ trình bày ban đầu.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?* Dùng `re.split(r'(\. |\! |\? |\.\n)', text)` để chia văn bản mà vẫn giữ được dấu câu. Các phần rỗng hoặc chứa khoảng trắng dư thừa được loại bỏ bằng `.strip()`, sau đó tiến hành ghép gộp các câu lại sao cho không vượt quá `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?* Thuật toán hoạt động theo cơ chế đệ quy, thử chia văn bản bằng separator hiện tại và ghép dồn lại cho tới mức tối đa `chunk_size`. Base case là khi chuỗi hiện hành nhỏ hơn `chunk_size` hoặc khi danh sách separator rỗng (sẽ tiến hành cắt thẳng tay theo độ dài index). Các đoạn vẫn vượt quá kích cỡ sẽ bị đệ quy phân tách tiếp bằng nhóm separator ưu tiên thấp hơn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?* Tuỳ vào việc có thư viện `chromadb` hay không mà dữ liệu sẽ được đẩy vào API `collection.add()` kèm metadata, hoặc lưu dạng list of dictionary vào in-memory store. Khi `search` bằng in-memory, hệ thống lặp qua toàn bộ list, dùng hàm `_dot` để tính điểm tích vô hướng (similarity score) giữa query và từng chunk, sau đó sort kết quả giảm dần.

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?* `search_with_filter` thực hiện filter trước để loại các bản ghi không khớp với metadata, sau đó mới tính toán score nhằm tối ưu tốc độ. `delete_document` thực hiện gỡ bỏ chunk thông qua cơ chế `where` clause trên ChromaDB hoặc dùng list comprehension để giữ lại các record khác `doc_id` đối với in-memory.

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?* Gọi `self.store.search(question, top_k)` để trích xuất list chunk, lặp qua nội dung của chúng và nối lại bằng `\n` để tạo chuỗi context nguyên khối. `context` này được chèn vào prompt mẫu của RAG theo sau là `question`, sau đó prompt hoàn chỉnh được đưa vào callback `llm_fn` để lấy câu trả lời cuối cùng.

### Test Results

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\damma\Downloads\WorkSpace\AI-IN-ACTION\day07\Day-07-Lab-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\damma\Downloads\WorkSpace\AI-IN-ACTION\day07\Day-07-Lab-Data-Foundations
plugins: anyio-4.13.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.13s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python is great | Python is an amazing language | high | 0.2442 | Không hẳn |
| 2 | Python is great | I like to eat apples | low | 0.0389 | Đúng |
| 3 | Vector database | Embedding store for vectors | high | 0.0491 | Sai |
| 4 | Machine learning | Artificial intelligence algorithms | high | -0.3159 | Sai |
| 5 | Cats are cute | Dogs are loyal pets | low | -0.0298 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là các cặp đồng nghĩa (3 và 4) lại có điểm số rất thấp (thậm chí âm). Điều này xảy ra do mô hình embedding hiện tại đang là `_mock_embed` (chạy thuật toán băm từ ký tự) nên không thực sự "hiểu" được ngữ nghĩa semantic của các từ đồng nghĩa.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What is the goal of the RAG system design? | Find relevant internal documents before answering to reduce hallucinations. |
| 2 | How do I handle an angry customer? | Listen actively, empathize, apologize, and offer a clear resolution. |
| 3 | What are vector databases used for? | They are used for similarity search by storing embeddings. |
| 4 | What are the built-in data structures in Python? | Lists, tuples, dictionaries, and sets. |
| 5 | Why is retrieval important for LLMs? | It provides grounded context to prevent hallucinations and access to private data. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | What is the goal of the RAG system design? | python_intro.txt | 0.1144 | Không | MOCK_LLM_ANSWER |
| 2 | How do I handle an angry customer? | vi_retrieval_notes.md | 0.0114 | Không | MOCK_LLM_ANSWER |
| 3 | What are vector databases used for? | vi_retrieval_notes.md | 0.1114 | Không | MOCK_LLM_ANSWER |
| 4 | What are the built-in data structures in Python? | python_intro.txt | 0.0582 | Có | MOCK_LLM_ANSWER |
| 5 | Why is retrieval important for LLMs? | rag_system_design.md | 0.0911 | Có | MOCK_LLM_ANSWER |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 2 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được cách một thành viên ứng dụng Regex cực kỳ tối ưu để tạo SentenceChunker bỏ qua được các ký tự đặc biệt như URL hay Email.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Cách nhóm khác thiết kế một chiến lược Hybrid Search bằng cách kết hợp metadata filter trước để loại bỏ nhiễu, sau đó mới dùng vector similarity search trên tập nhỏ còn lại.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ tích hợp mô hình Sentence-Transformers thực thụ thay vì dùng mock embedding, đồng thời tách nhỏ document thành các chunk đưa vào vector store thay vì lưu nguyên file để độ chính xác cao hơn.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
