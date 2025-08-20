# Robo-Advisor Chatbot Technical Architecture
*Updated: December 2024*

## 🏗️ **System Architecture Overview**

### **Two-VM Architecture for Dependency Resolution**

Our architecture uses **two separate virtual machines** to resolve fundamental dependency conflicts between existing tools and new chatbot requirements:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VM 1 (Port 8000)                                │
│                    Existing Portfolio Analysis Tools                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Portfolio Assessment (CSV parsing, AI analysis)                         │
│ • Life Insurance Calculator                                               │
│ • Assessment Forms & APIs                                                 │
│ • Dependencies: openai==1.3.7, pydantic<2.0, numpy/pandas                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP API Calls
                                    │ (Tool Integration)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VM 2 (Port 8001)                                │
│                        New Robo-Advisor Chatbot                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Semantic Intent Classification                                          │
│ • Smart Router & RAG System                                              │
│ • Calculator Selection & Integration                                     │
│ • File Processing & Analysis                                             │
│ • WebSocket Chat Interface                                               │
│ • Dependencies: openai>=1.99.9, pydantic>=2.0, langchain ecosystem      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket/HTTP
                                    │ (User Interface)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Port 3000)                            │
│                              Next.js App                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Robo-Advisor Chat Interface                                            │
│ • Portfolio Assessment Forms                                             │
│ • Life Insurance Assessment Forms                                        │
│ • Dashboard & Navigation                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Integration Flow:**
1. **User interacts** with chatbot on Port 8001
2. **Chatbot routes** to appropriate tools on Port 8000 when needed
3. **Tools complete** analysis and send reports back to chatbot
4. **Chatbot provides** in-chat Q&A of returned reports
5. **Seamless experience** across both systems

## 🧠 **Core Architecture: Semantic Understanding Flow**

### **1. Intent Classification Layer**
```python
class SemanticIntentClassifier:
    """Uses pure LLM-based semantic understanding, no keyword matching"""
    
    def __init__(self):
        self.llm = OpenAI(model="gpt-4", temperature=0.1)
        self.context_analyzer = ConversationContextAnalyzer()
    
    async def classify_intent_semantically(self, query: str, chat_history: List[Message]) -> IntentResult:
        # Extract semantic context from conversation
        semantic_context = self.context_analyzer.extract_semantic_context(chat_history)
        
        # Use LLM for deep semantic understanding
        intent_result = await self.llm.generate(
            self.build_semantic_intent_prompt(query, semantic_context)
        )
        
        return self.parse_semantic_intent(intent_result)
    
    def build_semantic_intent_prompt(self, query: str, context: SemanticContext) -> str:
        return f"""
        You are an expert financial advisor assistant. Understand the semantic meaning and intent behind this query.
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level}
        - Previous conversation themes: {context.semantic_themes}
        - Expressed goals: {context.user_goals}
        - Current focus area: {context.current_topic}
        
        **Current Query:** "{query}"
        
        **Semantic Analysis Required:**
        - What is the user REALLY asking for? (not just surface-level words)
        - What is their underlying goal or need?
        - What type of analysis would best serve their intent?
        - Are they looking for education, calculation, analysis, or guidance?
        
        **Intent Categories:**
        1. life_insurance_education - Learning about concepts, products, strategies
        2. insurance_needs_calculation - Wanting to determine coverage amounts
        3. portfolio_integration_analysis - Understanding insurance in financial context
        4. client_assessment_support - Helping assess client situations
        5. product_comparison - Comparing different insurance options
        6. scenario_analysis - "What if" questions and planning
        
        **Calculator Type Detection:**
        - quick_calculation: Simple, fast estimate needed
        - detailed_assessment: Comprehensive analysis required
        - portfolio_analysis: Portfolio-focused insurance analysis
        
        Return JSON with semantic understanding:
        {{
            "intent": "category",
            "semantic_goal": "what they really want",
            "calculator_type": "quick|detailed|portfolio",
            "confidence": 0.95,
            "reasoning": "why this classification",
            "follow_up_clarification": "questions to confirm understanding"
        }}
        """
```

### **2. Smart Router Layer**
```python
class SemanticSmartRouter:
    """Routes queries based on semantic understanding and confidence scores"""
    
    def __init__(self):
        self.rag_system = SemanticRAGSystem()
        self.external_search = ExternalSearchSystem()
        self.tool_integrator = ToolIntegrator()
        self.base_llm = BaseLLMResponse()
    
    async def route_query_semantically(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Make routing decisions based on semantic understanding"""
        
        if intent.calculator_type:
            # Route to appropriate calculator
            return await self.route_to_calculator(intent, context)
        
        elif intent.intent in ["life_insurance_education", "product_comparison", "scenario_analysis"]:
            # Try RAG first, then external search
            return await self.route_to_knowledge_sources(intent, context)
        
        else:
            # Fallback to base LLM for safe content
            return RoutingDecision(
                route_type="base_llm",
                confidence=0.7,
                reasoning="Safe fallback for general questions"
            )
    
    async def route_to_calculator(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to appropriate calculator based on semantic analysis"""
        
        if intent.calculator_type == "quick":
            return RoutingDecision(
                route_type="quick_calculator",
                confidence=intent.confidence,
                reasoning="Quick calculation requested"
            )
        
        elif intent.calculator_type in ["detailed", "portfolio"]:
            return RoutingDecision(
                route_type="external_tool",
                tool_type=intent.calculator_type,
                confidence=intent.confidence,
                reasoning="Comprehensive analysis required"
            )
    
    async def route_to_knowledge_sources(self, intent: IntentResult, context: ConversationContext) -> RoutingDecision:
        """Route to RAG, external search, or fallback based on confidence"""
        
        # Try RAG first
        rag_result = await self.rag_system.get_semantic_response(intent.query, context)
        
        if rag_result.quality_score > 0.8:
            return RoutingDecision(
                route_type="rag",
                confidence=rag_result.quality_score,
                reasoning="High-quality RAG response available"
            )
        
        # Try external search
        search_result = await self.external_search.search_with_evaluation(intent.query, context)
        
        if search_result.quality_score > 0.7:
            return RoutingDecision(
                route_type="external_search",
                confidence=search_result.quality_score,
                reasoning="External search provided quality information"
            )
        
        # Fallback to base LLM
        return RoutingDecision(
            route_type="base_llm",
            confidence=0.6,
            reasoning="Insufficient information from RAG and search"
        )
```

### **3. Response Generation Layer**
```python
class SemanticResponseGenerator:
    """Generates responses with deep semantic understanding"""
    
    def __init__(self):
        self.rag_generator = RAGResponseGenerator()
        self.search_generator = SearchResponseGenerator()
        self.calculator_generator = CalculatorResponseGenerator()
        self.base_generator = BaseResponseGenerator()
    
    async def generate_semantic_response(self, routing_decision: RoutingDecision, context: ConversationContext) -> GeneratedResponse:
        """Generate response based on routing decision and semantic context"""
        
        if routing_decision.route_type == "rag":
            return await self.rag_generator.generate_semantic_response(
                routing_decision, context
            )
        
        elif routing_decision.route_type == "external_search":
            return await self.search_generator.generate_semantic_response(
                routing_decision, context
            )
        
        elif routing_decision.route_type == "quick_calculator":
            return await self.calculator_generator.generate_quick_calculation_response(
                routing_decision, context
            )
        
        elif routing_decision.route_type == "external_tool":
            return await self.calculator_generator.generate_external_tool_response(
                routing_decision, context
            )
        
        else:  # base_llm fallback
            return await self.base_generator.generate_safe_response(
                routing_decision, context
            )
    
    async def enhance_with_semantic_context(self, response: str, context: ConversationContext) -> str:
        """Enhance response with semantic understanding of conversation context"""
        
        prompt = f"""
        Enhance this response to demonstrate deep semantic understanding of the user's needs:
        
        **Original Response:** "{response}"
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level}
        - Previous conversation themes: {context.semantic_themes}
        - Current focus area: {context.current_topic}
        - Expressed goals: {context.user_goals}
        
        **Enhancement Requirements:**
        1. **Context Continuity**: Build naturally on previous conversation
        2. **Knowledge Level**: Match the user's expertise level
        3. **Goal Orientation**: Align with their financial objectives
        4. **Natural Flow**: Make conversation feel continuous
        
        **Response Style:**
        - Beginner: Clear explanations with examples
        - Intermediate: Insights and deeper analysis
        - Expert: Advanced strategies and nuances
        
        Enhanced response:
        """
        
        enhanced_response = await self.llm.generate(prompt)
        return enhanced_response
```

## 🧮 **Calculator Integration Architecture**

### **Quick Calculator (In-Chat - Port 8001)**
```python
class QuickCalculatorAgent:
    """Handles quick insurance needs calculation in-chat"""
    
    def __init__(self):
        self.backend_api = BackendAPIClient()
        self.conversation_handler = ConversationHandler()
    
    async def handle_quick_calculation(self, query: str, context: ConversationContext) -> str:
        """Handle quick calculation with conversational data collection"""
        
        # Extract calculation intent
        calculation_intent = await self.extract_calculation_intent(query, context)
        
        if calculation_intent.needs_more_info:
            # Ask for missing information conversationally
            return await self.collect_missing_information(calculation_intent, context)
        
        else:
            # Perform calculation using existing backend API
            calculation_result = await self.backend_api.calculate_needs(
                calculation_intent.extracted_data
            )
            
            # Generate natural language response
            return await self.generate_calculation_response(calculation_result, context)
    
    async def collect_missing_information(self, intent: CalculationIntent, context: ConversationContext) -> str:
        """Collect missing information through natural conversation"""
        
        missing_fields = intent.missing_fields
        
        if len(missing_fields) == 1:
            return f"I'd be happy to help calculate your insurance needs! I just need to know your {missing_fields[0]}. What is your {missing_fields[0]}?"
        
        else:
            fields_text = ", ".join(missing_fields[:-1]) + f" and {missing_fields[-1]}"
            return f"Great! To calculate your insurance needs, I'll need a few details: {fields_text}. Let's start with your {missing_fields[0]} - what is it?"
    
    async def generate_calculation_response(self, result: CalculationResult, context: ConversationContext) -> str:
        """Generate natural language response for calculation results"""
        
        prompt = f"""
        Generate a natural, helpful response for insurance needs calculation results:
        
        **Calculation Results:**
        - Recommended Coverage: ${result.recommended_coverage:,}
        - Monthly Premium Estimate: ${result.monthly_premium:,}
        - Key Factors: {result.key_factors}
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level}
        - Previous Questions: {context.semantic_themes}
        
        **Response Requirements:**
        - Explain results clearly and naturally
        - Provide context about what the numbers mean
        - Offer next steps or additional questions
        - Match user's knowledge level
        
        Natural response:
        """
        
        response = await self.llm.generate(prompt)
        return response
```

### **External Tool Integration (Port 8000)**
```python
class ExternalToolIntegrator:
    """Handles routing to external tools on Port 8000 and report integration"""
    
    def __init__(self):
        self.tool_urls = {
            "detailed_assessment": "http://localhost:8000/assessment",
            "portfolio_analysis": "http://localhost:8000/portfolio-assessment"
        }
        self.webhook_handler = WebhookHandler()
    
    async def route_to_external_tool(self, tool_type: str, context: ConversationContext) -> ToolResponse:
        """Route user to external tool on Port 8000 with context preservation"""
        
        tool_url = self.tool_urls.get(tool_type)
        if not tool_url:
            raise ValueError(f"Unknown tool type: {tool_type}")
        
        # Generate unique session ID for context preservation
        session_id = self.generate_session_id(context)
        
        # Create deep link with context
        deep_link = f"{tool_url}?session_id={session_id}&return_to=robo-advisor"
        
        # Store context for when user returns
        await self.store_tool_context(session_id, context)
        
        return ToolResponse(
            tool_type=tool_type,
            action="open_external",
            url=deep_link,
            message=self.generate_tool_routing_message(tool_type, context),
            session_id=session_id
        )
    
    def generate_tool_routing_message(self, tool_type: str, context: ConversationContext) -> str:
        """Generate message explaining the tool routing"""
        
        if tool_type == "detailed_assessment":
            return """
            I understand you want a comprehensive analysis of your insurance needs. 
            I'll open our detailed assessment tool in a new tab where you can provide 
            comprehensive information about your situation.
            
            Once you complete the assessment, the detailed report will be sent back 
            to our chat where you can download it and ask me questions about it.
            
            Opening the detailed assessment tool now...
            """
        
        elif tool_type == "portfolio_analysis":
            return """
            You're looking for portfolio-focused insurance analysis. I'll open our 
            portfolio assessment tool in a new tab where you can upload your portfolio 
            and get a comprehensive analysis.
            
            When you're done, the portfolio analysis report will be sent back to our 
            chat for you to review and discuss with me.
            
            Opening the portfolio analysis tool now...
            """
    
    async def handle_report_return(self, session_id: str, report_data: ReportData) -> ReportIntegrationResult:
        """Handle reports returned from external tools on Port 8000"""
        
        # Retrieve stored context
        context = await self.retrieve_tool_context(session_id)
        
        # Process and store report
        processed_report = await self.process_report(report_data)
        
        # Generate welcome back message
        welcome_message = await self.generate_welcome_back_message(processed_report, context)
        
        return ReportIntegrationResult(
            session_id=session_id,
            report=processed_report,
            welcome_message=welcome_message,
            context=context
        )
```

## 🔍 **RAG & Search Architecture**

### **Semantic RAG System**
```python
class SemanticRAGSystem:
    """RAG system with deep semantic understanding"""
    
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = OpenAI(model="gpt-4", temperature=0.1)
    
    async def get_semantic_response(self, query: str, context: ConversationContext) -> RAGResult:
        """Get response using semantic understanding"""
        
        # Semantic query expansion
        expanded_queries = await self.semantically_expand_query(query, context)
        
        # Semantic document retrieval
        relevant_docs = await self.semantic_retrieval(expanded_queries, context)
        
        # Semantic response generation
        response = await self.generate_semantic_response(query, relevant_docs, context)
        
        # Semantic quality evaluation
        quality_score = await self.semantically_evaluate_quality(query, response, relevant_docs)
        
        return RAGResult(
            response=response,
            quality_score=quality_score,
            source_documents=relevant_docs,
            semantic_queries=expanded_queries
        )
    
    async def semantically_expand_query(self, query: str, context: ConversationContext) -> List[str]:
        """Expand query semantically based on context and intent"""
        
        prompt = f"""
        Expand this query semantically to capture the full intent and related concepts:
        
        **Original Query:** "{query}"
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level}
        - Previous questions: {context.semantic_themes}
        - Current focus: {context.current_topic}
        
        **Semantic Expansion Required:**
        - What related concepts should be included?
        - What underlying questions might they have?
        - What context would make this more comprehensive?
        
        Generate 3-5 semantically related queries that capture the full scope of their intent.
        
        Expanded Queries:
        """
        
        response = await self.llm.generate(prompt)
        return self.parse_expanded_queries(response)
    
    async def semantic_retrieval(self, queries: List[str], context: ConversationContext) -> List[Document]:
        """Retrieve documents using semantic understanding"""
        
        # Get embeddings for expanded queries
        embeddings = []
        for query in queries:
            embedding = await self.embedding_model.embed_query(query)
            embeddings.append(embedding)
        
        # Semantic search with context awareness
        relevant_docs = await self.vector_store.similarity_search_by_vector(
            embeddings,
            k=10,
            filter=self.build_semantic_filter(context)
        )
        
        return relevant_docs
```

### **External Search Integration**
```python
class ExternalSearchSystem:
    """Handles external search with quality evaluation"""
    
    def __init__(self):
        self.tavily_client = TavilyClient()
        self.quality_evaluator = SearchQualityEvaluator()
        self.llm = OpenAI(model="gpt-4", temperature=0.1)
    
    async def search_with_evaluation(self, query: str, context: ConversationContext) -> SearchResult:
        """Search external sources with quality evaluation"""
        
        # Perform search
        search_results = await self.tavily_client.search(query)
        
        # Evaluate quality of results
        quality_scores = await self.evaluate_search_quality(search_results, query, context)
        
        # Filter and rank results
        filtered_results = self.filter_by_quality(search_results, quality_scores, threshold=0.6)
        
        # Generate response from high-quality results
        if filtered_results:
            response = await self.generate_search_response(filtered_results, query, context)
            overall_quality = self.calculate_overall_quality(quality_scores, filtered_results)
        else:
            response = "I couldn't find reliable information on this topic from external sources."
            overall_quality = 0.0
        
        return SearchResult(
            response=response,
            quality_score=overall_quality,
            source_results=filtered_results,
            original_query=query
        )
    
    async def evaluate_search_quality(self, results: List[SearchResult], query: str, context: ConversationContext) -> List[float]:
        """Evaluate quality of search results using semantic understanding"""
        
        quality_scores = []
        
        for result in results:
            prompt = f"""
            Evaluate the quality and relevance of this search result:
            
            **Query:** "{query}"
            **Search Result:** "{result.content}"
            
            **Evaluation Criteria:**
            1. **Relevance**: How well does this address the query?
            2. **Accuracy**: Is the information likely to be correct?
            3. **Completeness**: Does it provide sufficient information?
            4. **Timeliness**: Is the information current?
            5. **Authority**: Is the source credible?
            
            **User Context:**
            - Knowledge Level: {context.knowledge_level}
            - Focus Area: {context.current_topic}
            
            Rate each criterion 0-1 and provide overall quality score.
            
            Quality Evaluation:
            """
            
            evaluation = await self.llm.generate(prompt)
            quality_score = self.parse_quality_evaluation(evaluation)
            quality_scores.append(quality_score)
        
        return quality_scores
```

## 📊 **Quality Evaluation Architecture**

### **Multi-Layer Evaluation System**
```python
class SemanticQualityEvaluator:
    """Evaluates response quality using semantic understanding"""
    
    def __init__(self):
        self.ragas_evaluator = RAGASEvaluator()
        self.semantic_evaluator = SemanticQualityEvaluator()
        self.user_satisfaction = UserSatisfactionEvaluator()
    
    async def evaluate_response_quality(self, query: str, response: str, context: ConversationContext) -> QualityScore:
        """Comprehensive quality evaluation"""
        
        # RAGAS evaluation
        ragas_scores = await self.ragas_evaluator.evaluate(query, response, context)
        
        # Semantic quality evaluation
        semantic_scores = await self.semantic_evaluator.evaluate(query, response, context)
        
        # User satisfaction prediction
        satisfaction_score = await self.user_satisfaction.predict_satisfaction(query, response, context)
        
        # Combine scores with weights
        overall_score = self.combine_quality_scores(ragas_scores, semantic_scores, satisfaction_score)
        
        return QualityScore(
            overall_score=overall_score,
            ragas_scores=ragas_scores,
            semantic_scores=semantic_scores,
            satisfaction_score=satisfaction_score,
            improvement_areas=self.identify_improvement_areas(ragas_scores, semantic_scores)
        )
    
    async def semantically_evaluate_quality(self, query: str, response: str, context: ConversationContext) -> SemanticQualityScore:
        """Evaluate quality based on semantic understanding"""
        
        prompt = f"""
        Evaluate this response using semantic understanding of the user's needs:
        
        **User Query:** "{query}"
        **Generated Response:** "{response}"
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level}
        - Previous questions: {context.semantic_themes}
        - Expressed goals: {context.user_goals}
        
        **Semantic Quality Criteria:**
        1. **Intent Alignment**: Does it address what they REALLY want? (0-1)
        2. **Context Continuity**: Does it build naturally on the conversation? (0-1)
        3. **Knowledge Appropriateness**: Is it at the right level for them? (0-1)
        4. **Goal Relevance**: Does it serve their financial goals? (0-1)
        5. **Semantic Completeness**: Does it cover the full scope of their intent? (0-1)
        
        **Scoring (0-1 for each criterion):**
        - Intent Alignment: [score] - [reasoning]
        - Context Continuity: [score] - [reasoning]
        - Knowledge Appropriateness: [score] - [reasoning]
        - Goal Relevance: [score] - [reasoning]
        - Semantic Completeness: [score] - [reasoning]
        
        **Overall Semantic Quality Score:** [average]
        **Key Improvement Areas:** [specific suggestions]
        """
        
        evaluation = await self.llm.generate(prompt)
        return self.parse_semantic_evaluation(evaluation)
```

### **Quality Improvement Agents**
```python
class QualityImprovementAgent:
    """Improves low-quality responses using agent-based approach"""
    
    def __init__(self):
        self.analysis_agent = QualityAnalysisAgent()
        self.improvement_agent = ResponseImprovementAgent()
        self.validation_agent = QualityValidationAgent()
    
    async def improve_low_quality_response(self, response: str, evaluation: QualityScore, context: ConversationContext) -> ImprovedResponse:
        """Improve response quality through agent collaboration"""
        
        # Analyze improvement areas
        improvement_plan = await self.analysis_agent.analyze_improvement_areas(evaluation, context)
        
        # Generate improved response
        improved_response = await self.improvement_agent.improve_response(
            response, improvement_plan, context
        )
        
        # Validate improvement
        validation_result = await self.validation_agent.validate_improvement(
            response, improved_response, evaluation, context
        )
        
        if validation_result.improved:
            return ImprovedResponse(
                original_response=response,
                improved_response=improved_response,
                improvement_plan=improvement_plan,
                quality_improvement=validation_result.quality_improvement
            )
        else:
            # If improvement failed, return original with explanation
            return ImprovedResponse(
                original_response=response,
                improved_response=response,
                improvement_plan=improvement_plan,
                quality_improvement=0.0,
                improvement_failed=True,
                failure_reason=validation_result.failure_reason
            )
```

## 🔒 **Compliance & Safety Architecture**

### **Compliance Agent**
```python
class ComplianceAgent:
    """Ensures compliance with financial regulations and legal requirements"""
    
    def __init__(self):
        self.legal_checker = LegalComplianceChecker()
        self.risk_assessor = RiskAssessmentAgent()
        self.disclaimer_generator = DisclaimerGenerator()
        self.response_rewriter = ResponseRewriter()
    
    async def review_response(self, response: str, context: ConversationContext) -> ComplianceResult:
        """Review response for compliance and safety"""
        
        # Legal compliance check
        legal_compliance = await self.legal_checker.check_compliance(response, context)
        
        # Risk assessment
        risk_assessment = await self.risk_assessor.assess_risk(response, context)
        
        # Generate necessary disclaimers
        disclaimers = await self.disclaimer_generator.generate_disclaimers(
            response, legal_compliance, risk_assessment
        )
        
        # Determine if response needs rewriting
        needs_rewriting = self.determine_rewriting_needs(legal_compliance, risk_assessment)
        
        if needs_rewriting:
            rewritten_response = await self.response_rewriter.rewrite_for_compliance(
                response, legal_compliance, risk_assessment, context
            )
        else:
            rewritten_response = response
        
        return ComplianceResult(
            original_response=response,
            final_response=rewritten_response,
            legal_compliance=legal_compliance,
            risk_assessment=risk_assessment,
            disclaimers=disclaimers,
            was_rewritten=needs_rewriting
        )
    
    async def assess_risk(self, response: str, context: ConversationContext) -> RiskAssessment:
        """Assess potential risks in the response"""
        
        prompt = f"""
        Assess the potential risks in this financial advice response:
        
        **Response:** "{response}"
        
        **Risk Categories to Assess:**
        1. **Financial Risk**: Could this advice lead to financial loss?
        2. **Regulatory Risk**: Does this violate financial regulations?
        3. **Liability Risk**: Could this create legal liability?
        4. **Misunderstanding Risk**: Could this be misinterpreted?
        5. **Compliance Risk**: Does this meet compliance standards?
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level}
        - Previous Questions: {context.semantic_themes}
        
        **Risk Assessment (0-1 for each category):**
        - Financial Risk: [score] - [reasoning]
        - Regulatory Risk: [score] - [reasoning]
        - Liability Risk: [score] - [reasoning]
        - Misunderstanding Risk: [score] - [reasoning]
        - Compliance Risk: [score] - [reasoning]
        
        **Overall Risk Level:** [low|medium|high]
        **Risk Mitigation Required:** [yes|no]
        **Specific Mitigation Actions:** [list actions]
        """
        
        risk_assessment = await self.llm.generate(prompt)
        return self.parse_risk_assessment(risk_assessment)
```

## 🔧 **Technical Implementation Details**

### **Backend Architecture (Port 8001 - New VM)**
```python
# FastAPI Application Structure
app = FastAPI(title="Robo-Advisor Chatbot API", version="1.0.0")

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Initialize chat session
    chat_session = ChatSession(session_id=session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message through semantic pipeline
            response = await process_message_semantically(message, chat_session)
            
            # Send response
            await websocket.send_text(json.dumps(response))
    
    except WebSocketDisconnect:
        # Clean up session
        await chat_session.cleanup()

# HTTP endpoints for tool integration
@app.post("/api/chat/process")
async def process_chat_message(message: ChatMessage):
    """Process chat message through semantic pipeline"""
    
    # Intent classification
    intent = await semantic_intent_classifier.classify_intent_semantically(
        message.content, message.context
    )
    
    # Smart routing
    routing_decision = await smart_router.route_query_semantically(intent, message.context)
    
    # Response generation
    response = await response_generator.generate_semantic_response(
        routing_decision, message.context
    )
    
    # Quality check
    quality_score = await quality_evaluator.evaluate_response_quality(
        message.content, response.content, message.context
    )
    
    # Compliance review
    compliance_result = await compliance_agent.review_response(
        response.content, message.context
    )
    
    return ChatResponse(
        content=compliance_result.final_response,
        quality_score=quality_score.overall_score,
        routing_decision=routing_decision,
        disclaimers=compliance_result.disclaimers
    )
```

### **Frontend Architecture**
```typescript
// Next.js App Router Structure
// app/robo-advisor/page.tsx - Main chat interface
// app/robo-advisor/components/ - Chat components
// app/robo-advisor/api/ - API routes

// WebSocket Connection Management
class ChatWebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private messageQueue: ChatMessage[] = [];
  
  constructor(sessionId: string) {
    this.sessionId = sessionId;
    this.connect();
  }
  
  private connect() {
    this.ws = new WebSocket(`ws://localhost:8001/ws/chat/${this.sessionId}`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected to chatbot on Port 8001');
      this.processMessageQueue();
    };
    
    this.ws.onmessage = (event) => {
      const response = JSON.parse(event.data);
      this.handleResponse(response);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      setTimeout(() => this.connect(), 1000);
    };
  }
  
  public sendMessage(message: ChatMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message);
    }
  }
  
  private processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) this.sendMessage(message);
    }
  }
}

// Chat Component with Semantic Understanding
const RoboAdvisorChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  
  const wsManager = useRef<ChatWebSocketManager | null>(null);
  
  useEffect(() => {
    // Initialize WebSocket connection to Port 8001
    wsManager.current = new ChatWebSocketManager(generateSessionId());
    
    // Add welcome message
    setMessages([{
      id: 'welcome',
      type: 'assistant',
      content: 'Hello! I\'m your AI financial advisor. I can help you with life insurance questions, coverage calculations, and portfolio analysis. What would you like to know?',
      timestamp: new Date()
    }]);
  }, []);
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
      files: uploadedFiles
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setUploadedFiles([]);
    setIsTyping(true);
    
    // Send message through WebSocket to Port 8001
    wsManager.current?.sendMessage(userMessage);
  };
  
  const handleResponse = (response: ChatResponse) => {
    const assistantMessage: ChatMessage = {
      id: generateMessageId(),
      type: 'assistant',
      content: response.content,
      timestamp: new Date(),
      qualityScore: response.quality_score,
      routingDecision: response.routing_decision,
      disclaimers: response.disclaimers
    };
    
    setMessages(prev => [...prev, assistantMessage]);
    setIsTyping(false);
  };
  
  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <ChatMessageComponent 
            key={message.id} 
            message={message} 
          />
        ))}
        {isTyping && <TypingIndicator />}
      </div>
      
      {/* File Upload Area */}
      <FileUploadArea 
        files={uploadedFiles}
        onFilesChange={setUploadedFiles}
      />
      
      {/* Input Area */}
      <ChatInput 
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSendMessage}
        disabled={isTyping}
      />
    </div>
  );
};
```

## 🚀 **Deployment & Performance**

### **Two-VM Deployment Configuration**
```yaml
# docker-compose.yml for Port 8001 (New Chatbot VM)
version: '3.8'
services:
  chatbot_backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - QDRANT_URL=http://qdrant:6333
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - EXISTING_TOOLS_URL=http://localhost:8000  # Port 8000 tools
    depends_on:
      - qdrant
      - redis
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_CHATBOT_URL=http://localhost:8001
      - NEXT_PUBLIC_TOOLS_URL=http://localhost:8000
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  qdrant_data:
  redis_data:
```

### **Performance Optimization**
```python
# Caching Strategy
class SemanticCache:
    """Intelligent caching for semantic responses"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = 3600  # 1 hour
    
    async def get_cached_response(self, query_hash: str, context_hash: str) -> Optional[str]:
        """Get cached response if available"""
        cache_key = f"semantic_response:{query_hash}:{context_hash}"
        return self.redis_client.get(cache_key)
    
    async def cache_response(self, query_hash: str, context_hash: str, response: str):
        """Cache response for future use"""
        cache_key = f"semantic_response:{query_hash}:{context_hash}"
        self.redis_client.setex(cache_key, self.cache_ttl, response)

# Async Processing
class AsyncMessageProcessor:
    """Process messages asynchronously for better performance"""
    
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.workers = []
        self.start_workers()
    
    async def start_workers(self, num_workers: int = 3):
        """Start worker tasks for processing messages"""
        for i in range(num_workers):
            worker = asyncio.create_task(self.worker_task(f"worker-{i}"))
            self.workers.append(worker)
    
    async def worker_task(self, worker_name: str):
        """Worker task for processing messages"""
        while True:
            try:
                message = await self.task_queue.get()
                await self.process_message(message)
                self.task_queue.task_done()
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
    
    async def process_message(self, message: ChatMessage):
        """Process individual message"""
        # Process message through semantic pipeline
        response = await self.semantic_pipeline.process(message)
        
        # Send response back to client
        await self.send_response(message.session_id, response)
```

## 📈 **Monitoring & Evaluation**

### **LangSmith Integration**
```python
# LangSmith monitoring setup
import os
from langsmith import Client

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "robo-advisor-chatbot"

langsmith_client = Client()

# Monitor semantic pipeline
@langsmith_client.trace
async def semantic_pipeline_process(message: ChatMessage) -> ChatResponse:
    """Process message through semantic pipeline with monitoring"""
    
    # Intent classification
    with langsmith_client.trace("intent_classification") as intent_trace:
        intent = await semantic_intent_classifier.classify_intent_semantically(
            message.content, message.context
        )
        intent_trace.add_metadata({
            "confidence": intent.confidence,
            "intent_type": intent.intent,
            "calculator_type": intent.calculator_type
        })
    
    # Smart routing
    with langsmith_client.trace("smart_routing") as routing_trace:
        routing_decision = await smart_router.route_query_semantically(intent, message.context)
        routing_trace.add_metadata({
            "route_type": routing_decision.route_type,
            "confidence": routing_decision.confidence,
            "reasoning": routing_decision.reasoning
        })
    
    # Response generation
    with langsmith_client.trace("response_generation") as response_trace:
        response = await response_generator.generate_semantic_response(
            routing_decision, message.context
        )
        response_trace.add_metadata({
            "response_length": len(response.content),
            "generation_method": routing_decision.route_type
        })
    
    return response
```

### **RAGAS Evaluation**
```python
# RAGAS evaluation setup
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

async def evaluate_rag_quality(query: str, response: str, context: List[str]) -> Dict[str, float]:
    """Evaluate RAG response quality using RAGAS"""
    
    # Prepare data for RAGAS
    dataset = Dataset.from_dict({
        "question": [query],
        "answer": [response],
        "contexts": [context]
    })
    
    # Run evaluation
    results = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
    )
    
    return {
        "faithfulness": results["faithfulness"],
        "answer_relevancy": results["answer_relevancy"],
        "context_precision": results["context_precision"],
        "context_recall": results["context_recall"],
        "overall_score": sum(results.values()) / len(results)
    }
```

## 🔄 **Current Implementation Status**

### **✅ Completed Components:**
- **Complete chatbot backend architecture** with all core components
- **Intent classification system** with semantic understanding
- **Smart router** with calculator selection logic
- **Quick calculator agent** for in-chat calculations
- **File processing system** for uploads and analysis
- **RAG system foundation** with Qdrant integration
- **External search system** with Tavily integration
- **Tool integrator** for external tool routing
- **WebSocket API** for real-time chat
- **Quality evaluation framework** with RAGAS integration
- **Two-VM architecture setup** and configuration

### **🔄 In Progress:**
- **Qdrant vector database setup** and ingest RAG documents
- **External tool routing** to Port 8000 tools
- **Report return system** from completed tools
- **End-to-end testing** of complete user flows

### **📋 Next Steps:**
1. **Complete Qdrant setup** and ingest RAG documents
2. **Test external tool routing** to existing tools on Port 8000
3. **Implement webhook system** for report returns
4. **Add compliance agent** and legal guardrails
5. **Performance testing** and optimization
6. **Production deployment** and monitoring setup

This technical architecture provides a comprehensive foundation for building a sophisticated, human-feeling chatbot with deep semantic understanding, intelligent routing, quality assurance, and compliance-first design - all while maintaining high performance and scalability. The two-VM architecture ensures we can maintain existing functionality while building the new chatbot with modern dependencies and advanced capabilities. 