# **AIE7 Certification Challenge - Project Answers**

## **Task 1: Defining your Problem and Audience**

### **Deliverable 1: Succinct Problem Description**

Financial advisors lack sufficient understanding of life insurance products, coverage calculations, and product selection criteria to confidently recommend life insurance as part of a diversified portfolio, causing them to avoid this integral component of risk management entirely.

### **Deliverable 2: Problem for Specific User**

**Target User**: Financial Advisors and Investment Professionals

Financial advisors face a fundamental knowledge gap when it comes to life insurance that prevents them from providing comprehensive financial planning services. Despite life insurance being an integral part of a diversified, risk-averse portfolio with safety nets, advisors often lack the deep understanding needed to confidently explain how life insurance works, determine appropriate coverage amounts, select the right product types for different client situations, and articulate the strategic benefits within a broader financial plan. This knowledge deficit creates significant barriers: advisors feel uncomfortable making life insurance recommendations, so they simply avoid the topic entirely, leaving clients without crucial protection and missing opportunities to provide truly comprehensive financial planning services.

This creates several critical problems: clients miss out on essential risk management tools that could protect their families and provide tax advantages, advisors lose potential revenue from life insurance commissions and comprehensive planning fees, and the overall financial planning relationship suffers from incomplete advice. Most concerning, this avoidance means clients may not have adequate protection in place, leaving families vulnerable to financial hardship in the event of premature death, while advisors miss opportunities to demonstrate their full value as comprehensive financial planners.

---

## **Task 2: Propose a Solution**

### **Deliverable 1: Proposed Solution**

Our solution is an **AI-Powered Life Insurance Knowledge Assistant** that transforms how financial advisors approach life insurance recommendations. In this better world, advisors gain the confidence and knowledge they need to seamlessly integrate life insurance into their comprehensive financial planning practice. The system provides instant access to deep life insurance expertise through a conversational interface that feels like consulting with a senior life insurance specialist in real-time.

When advisors need to discuss life insurance with clients, they simply ask questions in natural language and receive comprehensive, professional-grade responses that explain complex concepts clearly, provide accurate coverage calculations using multiple methodologies, and recommend appropriate product types based on client circumstances. The system automatically extracts relevant client information from conversations, performs sophisticated needs analysis, and presents recommendations with clear explanations of why specific products and coverage amounts are appropriate for each situation. This enables advisors to confidently present life insurance as a strategic component of portfolio diversification and risk management, rather than avoiding the topic entirely.

### **Deliverable 2: Tool Stack and Choices**

1. **LLM**: OpenAI GPT-4 - Provides the highest quality reasoning and response generation for complex financial scenarios, essential for accurate calculations and professional-grade explanations of life insurance concepts.

2. **Embedding Model**: OpenAI text-embedding-3-small - Offers optimal balance of performance and cost for semantic search across our extensive life insurance knowledge base.

3. **Orchestration**: LangGraph - Enables sophisticated multi-agent workflows with state management, perfect for coordinating knowledge retrieval, calculation, and recommendation agents while maintaining conversation context.

4. **Vector Database**: Qdrant - Provides high-performance similarity search with metadata filtering, crucial for retrieving relevant life insurance information from our comprehensive document collection.

5. **Monitoring**: LangSmith - Offers comprehensive tracing and debugging capabilities for complex multi-agent interactions, essential for maintaining system reliability and advisor confidence.

6. **Evaluation**: RAGAS - Provides industry-standard metrics for RAG system evaluation, ensuring our life insurance advice meets professional standards and accuracy requirements.

7. **User Interface**: Chainlit - Delivers a conversational interface that feels natural for financial advisors, with session management and context preservation for ongoing client conversations.

8. **Serving & Inference**: Local deployment with Uvicorn - Enables rapid development and testing while maintaining data privacy for sensitive financial information and advisor-client conversations.

### **Deliverable 3: Agent Usage**

**Multi-Agent Architecture**: We use agentic reasoning across four specialized agents organized in two teams:

**Research Team:**
1. **RAG Agent**: Handles retrieval and synthesis of life insurance information from our comprehensive document collection, providing accurate, contextual explanations of products, regulations, and best practices that advisors can confidently share with clients.

2. **Search Agent**: Conducts real-time market research using Tavily API to provide current rates, trends, and product comparisons, automatically triggered when advisors need up-to-date market information.

**Analysis Team:**
3. **Calculator Agent**: Performs intelligent data extraction from advisor conversations and applies multiple calculation methodologies (DIME, human life value, capital needs analysis) to provide comprehensive coverage recommendations with clear breakdowns and policy type suggestions tailored to each client's situation.

**Agentic Reasoning Benefits**: This approach enables sophisticated decision-making about which information sources to consult, when to perform calculations, and when to provide specific product recommendations - exactly the type of reasoning that experienced life insurance specialists perform, but made accessible to advisors who lack this specialized expertise.

---

## **Task 3: Dealing with the Data**

### **Deliverable 1: Data Sources and External APIs**

**RAG Data Sources:**
- **Core Knowledge Base**: 16 structured text files covering life insurance basics, product comparisons, portfolio integration, tax implications, calculation methods, and regulatory compliance
- **Industry Reports**: LIMRA Insurance Barometer Studies (2021-2024), quarterly technical reports, sales and applications data
- **Regulatory Documents**: NAIC compliance guide (13,001 lines), IRS publications (560, 590-B, 525), consumer protection guides
- **Educational Content**: Investopedia articles, Kaplinger content, due diligence guides for financial advisors

**External APIs:**
- **Tavily Search API**: Used for real-time market information, current rates, industry trends, specific company information, and recent regulatory changes. Enhanced queries include financial context (e.g., "life insurance current rates market conditions 2024 financial planning").

### **Deliverable 2: Default Chunking Strategy**

**Chunking Parameters:**
- **Chunk Size**: 1,000 tokens (optimized for GPT-4 context window)
- **Chunk Overlap**: 200 tokens (20% overlap for context continuity)
- **Length Function**: tiktoken-based token counting for accurate sizing

**Chunking Method:**
- **Primary**: RecursiveCharacterTextSplitter with semantic separators
- **Separators Priority**: `\n\n` (paragraph breaks), `\n` (line breaks), `. ` (sentence boundaries), ` ` (word boundaries), `""` (character-level fallback)

**Why This Strategy:**
- **Financial Document Optimization**: Keeps related financial concepts together, preserves complete regulatory statements, maintains calculation methodologies, and keeps product features intact
- **Retrieval Quality**: 200-token overlap ensures context continuity, 1,000 tokens provide sufficient detail for complex financial queries, and metadata enhancement includes source tracking
- **Production Considerations**: Optimized for OpenAI's pricing model, balances detail with context window constraints, and efficient for large document collections

### **Deliverable 3: Additional Data Requirements**

**Synthetic Test Data**: For RAGAS evaluation and performance benchmarking, covering all major life insurance topics and calculation scenarios.

**Performance Metrics Data**: Query logs for real user interaction patterns, response quality scores, and retrieval accuracy assessments.

**Advanced Retrieval Testing Data**: Multi-query variations, context-specific queries (portfolio analysis, tax planning, compliance), and edge cases requiring multiple information sources.

---

## **Task 5: Creating a Golden Test Data Set**

### **Deliverable 1: RAGAS Evaluation Results**

**Golden Test Dataset Generated**: Successfully created 28 high-quality test cases covering comprehensive life insurance topics including product comparisons, calculation methodologies, regulatory compliance, and client scenarios. The synthetic dataset was generated using RAGAS's synthetic data generation capabilities, ensuring diverse coverage of financial advisory use cases.

**Naive Basic Retriever RAGAS Evaluation Results**:

| Metric | Score | Assessment |
|--------|-------|------------|
| **Faithfulness** | 0.9571 | Excellent - Responses are highly faithful to source material |
| **Answer Relevancy** | 0.3935 | Good - Responses address user questions but room for improvement |
| **Context Precision** | 0.9286 | Excellent - Retrieved context is highly relevant |
| **Context Recall** | 0.5714 | Good - System retrieves relevant information but may miss some |
| **Average Score** | 0.7127 | **Good** - System performs well with room for optimization |
| **Average Cost** | $0.01 | Very cost-effective |
| **Average Latency** | 2.5s | Fast response times |

### **Deliverable 2: Performance Conclusions**

**System Performance Assessment**: Our Naive Basic Retriever demonstrates solid performance across all key RAGAS metrics, achieving an average score of 0.7127. The system excels in faithfulness (0.9571) and context precision (0.9286), indicating that responses are highly accurate and the retrieved context is highly relevant. The answer relevancy of 0.3935 shows good performance with room for improvement in directly addressing user questions.

**Key Performance Insights**:

1. **Excellent Faithfulness**: The high faithfulness score (0.9571) indicates minimal hallucination risk, providing confidence that responses are grounded in the source material.

2. **Strong Context Precision**: The excellent context precision (0.9286) shows that when the system retrieves documents, they are highly relevant to the query.

3. **Moderate Answer Relevancy**: The answer relevancy score (0.3935) indicates that while responses are faithful to the source material, they could be more directly tailored to address specific user questions.

4. **Good Context Recall**: The context recall score (0.5714) shows that the system retrieves relevant information but may miss some comprehensive details for complex queries.

5. **Cost-Effective Performance**: With an average cost of $0.01 per query and 2.5-second latency, the system provides excellent value for money.

**Areas for Improvement**: The system would benefit from enhanced query understanding and more sophisticated retrieval algorithms to improve answer relevancy and context recall. Advanced techniques like query expansion or multi-query retrieval could help address these limitations.

**Production Readiness**: With an average performance score of 0.7127 and excellent faithfulness, the Naive Basic Retriever provides a solid foundation for production deployment. The high faithfulness score ensures that advisors will receive accurate information, while the cost-effective performance makes it suitable for widespread use.

---

## **Task 6: The Benefits of Advanced Retrieval**

### **Deliverable 1: Advanced Retrieval Techniques Selection**

Based on my analysis of the financial advisory domain and the limitations identified in my Naive Basic Retriever evaluation, I selected four advanced retrieval techniques to implement and assess:

1. **Multi-Query Retriever**: This technique generates multiple query variations from a single user input to improve recall by addressing different aspects of complex financial queries, which could benefit comprehensive life insurance advice that often requires information from multiple perspectives (product features, calculations, regulations, and client scenarios).

2. **Ensemble Retriever**: This approach combines multiple retrieval strategies using rank-fusion to leverage the strengths of different retrieval methods, which could be particularly valuable for financial advisory queries that may benefit from both semantic similarity and keyword matching to capture both conceptual understanding and specific product terminology.

3. **Parent Document Retriever**: This technique retrieves smaller "child chunks" but returns larger "parent documents" for context, which could be ideal for financial documents where complete regulatory statements, calculation methodologies, and product descriptions need to be preserved in their full context for accurate advice.

4. **BM25 Retriever**: This keyword-based retrieval algorithm provides a baseline comparison to semantic approaches, which could be important for understanding whether financial domain queries benefit more from semantic understanding or traditional keyword matching, especially for specific product names, regulatory terms, and calculation formulas.

### **Deliverable 2: Advanced Retrieval Implementation**

**Implementation Strategy**: I developed a modular evaluation framework that allows me to test each advanced retrieval technique independently while reusing expensive shared resources (document loading, dataset generation, and base vector store creation). This approach could ensure efficient testing and prevent redundant API calls and computation.

**Multi-Query Retriever Implementation**: 
- Uses `MultiQueryRetriever.from_llm()` to generate multiple query variations
- Leverages GPT-4 to create diverse query perspectives from single user input
- Could improve recall by addressing different aspects of complex financial queries

**Ensemble Retriever Implementation**:
- Combines vector similarity search with BM25 keyword retrieval
- Uses equal weighting for rank-fusion across multiple retrieval strategies
- Could balance semantic understanding with keyword precision

**Parent Document Retriever Implementation**:
- Implements parent-child document splitting with different chunk sizes
- Uses `InMemoryStore` for parent document storage
- Could preserve complete context for regulatory and calculation content

**BM25 Retriever Implementation**:
- Uses `rank_bm25` library for keyword-based retrieval
- Provides baseline comparison to semantic approaches
- Tests effectiveness of keyword matching for financial terminology

**Evaluation Framework**: Each retriever is implemented as a standalone script that loads shared state (documents, dataset, vector store) and runs comprehensive RAGAS evaluation with the four core metrics: Faithfulness, Response Relevancy, Context Precision, and Context Recall.

---

## **Task 7: Assessing Performance**

### **Deliverable 1: Performance Comparison Results**

**Comprehensive RAGAS Evaluation Comparison**: I conducted thorough testing of all retrieval approaches using the RAGAS framework to quantify performance improvements over the original Naive Basic Retriever. The results reveal significant performance differences across retrieval strategies.

**Performance Comparison Table**:

| Retriever Type | Faithfulness | Answer Relevancy | Context Precision | Context Recall | Average Score | Avg Cost | Total Cost | Avg Latency |
|----------------|--------------|------------------|-------------------|----------------|---------------|----------|------------|-------------|
| **Naive Basic Retriever** | 0.9571 | 0.3935 | 0.9286 | 0.5714 | 0.7127 | $0.01 | $0.05 | 2.5s |
| **Multi-Query Retriever** | 0.9780 | 0.8050 | 0.8327 | 0.8915 | 0.8768 | $0.02 | $0.72 | 12.34s |
| **Ensemble Retriever** | 1.0000 | 0.8069 | 0.9651 | 0.6900 | 0.8655 | $0.04 | $0.20 | 7.76s |
| **Parent Document Retriever** | 0.9954 | 0.8011 | 0.7143 | 0.8000 | 0.8277 | $0.05 | $0.25 | 7.47s |
| **BM25 Retriever** | 0.8605 | 0.4030 | 0.4770 | 0.3909 | 0.5329 | $0.04 | $0.20 | 5.93s |

**Key Performance Insights**:

1. **Multi-Query Retriever Superior Performance**: Achieved the highest average score (0.8768) with significant improvements in answer relevancy (+104.6%) and context recall (+56.0%) compared to the Naive Basic Retriever, demonstrating the effectiveness of query expansion for complex financial queries.

2. **Ensemble Retriever Excellence**: Achieved perfect faithfulness (1.0000) and the highest context precision (0.9651), showing that combining multiple retrieval strategies could eliminate hallucination risk while maintaining high precision.

3. **Semantic Retrievers Outperform Keyword-Based**: All semantic approaches (Naive, Multi-Query, Ensemble, Parent Document) significantly outperformed the BM25 keyword-based retriever, highlighting the importance of semantic understanding for financial domain queries.

4. **Cost-Performance Trade-offs**: While Multi-Query achieved the best performance, it also had the highest latency (12.34s) and cost ($0.72 total). The Ensemble retriever provided a good balance of performance (0.8655) and reasonable cost ($0.20 total).

### **Deliverable 2: Future Application Improvements**

**Second Half Course Improvements**: Based on my performance analysis and identified limitations, I plan to implement several key improvements to enhance the application's effectiveness for financial advisory use cases.

**1. Fine-tuned Embedding Model Implementation**:
- I will implement a fine-tuned embedding model specifically trained on financial and insurance terminology to improve semantic understanding of domain-specific queries
- This could potentially improve answer relevancy scores by 15-20% and context recall by 10-15% based on similar implementations in financial domains

**2. Hybrid Retrieval Strategy Optimization**:
- I will develop a dynamic retrieval strategy that automatically selects the optimal retriever based on query complexity and type
- Simple queries could use the cost-effective Naive Basic Retriever, while complex financial planning queries could automatically trigger the Multi-Query or Ensemble approaches

**3. Portfolio Analysis Agent Implementation**:
- I will create a specialized portfolio analysis agent that supports uploading customer/prospect financial documents and provides detailed breakdowns of how life insurance could fit into that portfolio including what type, how much, and why
- This could enable personalized, data-driven life insurance recommendations based on actual client financial situations

**4. Context-Aware Response Generation**:
- I will develop a response generation system that considers the retrieved context quality and adjusts response style accordingly
- High-confidence retrievals could receive detailed responses, while lower-confidence retrievals could receive more conservative, fact-checking responses

**5. Real-time Performance Monitoring**:
- I will implement comprehensive monitoring using LangSmith to track performance metrics in production
- This will enable continuous optimization based on real user interaction patterns and feedback

**6. Advanced Chunking Strategies**:
- I will experiment with semantic chunking techniques that preserve complete financial concepts and regulatory statements
- This could improve context precision and recall for complex financial documents

**7. RAG Database Enhancement**:
- I will improve the RAG database to include additional documentation for increased answer quality, such as textbooks, more articles, more detailed product specifications for specific companies, and comprehensive regulatory guides
- This could significantly improve context recall and answer relevancy by providing more comprehensive and detailed source material

**Expected Performance Improvements**: These enhancements could potentially improve the overall average score from 0.8768 (Multi-Query) to 0.90+ while maintaining cost-effectiveness and reducing latency through optimized retrieval strategies.

