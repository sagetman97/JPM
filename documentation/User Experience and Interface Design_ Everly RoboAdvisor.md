
# User Experience and Interface Design: Everly RoboAdvisor

## User Personas

Understanding the target users is crucial for designing an effective and engaging user experience. The Everly RoboAdvisor will serve two primary user groups: JPMorgan financial advisors and their clients. Each group has distinct needs, goals, and pain points that must be addressed through thoughtful design.

### Primary Persona 1: JPMorgan Financial Advisor

**Name:** Sarah Chen  
**Age:** 34  
**Role:** Senior Financial Advisor at JPMorgan Private Bank  
**Experience:** 8 years in wealth management, 3 years at JPMorgan  

**Background:**
Sarah manages a portfolio of high-net-worth clients with assets ranging from $1M to $25M. She has a strong background in investment planning and estate planning but feels less confident when discussing life insurance products. She often relies on external insurance specialists for complex life insurance cases, which can slow down the client engagement process.

**Goals:**
- Provide comprehensive financial planning advice to clients
- Increase confidence in recommending life insurance products
- Streamline the insurance needs assessment process
- Enhance client relationships through better service delivery
- Meet quarterly sales targets while maintaining client satisfaction

**Pain Points:**
- Limited knowledge of complex life insurance products (IUL, VUL, etc.)
- Time-consuming process to research and explain insurance options
- Difficulty visualizing insurance benefits for clients
- Concerns about recommending inappropriate products
- Fragmented tools and systems for financial planning

**Technology Comfort:** High - comfortable with digital tools, uses multiple financial planning software platforms daily

**Preferred Interaction Style:** Efficient, data-driven, with quick access to detailed information when needed

### Primary Persona 2: JPMorgan Client (High-Net-Worth Individual)

**Name:** Michael Rodriguez  
**Age:** 45  
**Role:** CEO of a mid-sized technology company  
**Net Worth:** $8M (including business equity)  

**Background:**
Michael is a successful entrepreneur with a growing family (spouse and two teenage children). He has existing investment portfolios managed by JPMorgan but has limited life insurance coverage - only a basic term policy through his company. He's aware he may need additional coverage but finds insurance confusing and time-consuming to research.

**Goals:**
- Protect his family's financial future
- Optimize tax strategies for wealth transfer
- Understand how life insurance fits into his overall financial plan
- Make informed decisions quickly without extensive research
- Maintain his current lifestyle and business focus

**Pain Points:**
- Overwhelmed by insurance jargon and complex product features
- Uncertain about appropriate coverage amounts
- Skeptical about insurance as an investment vehicle
- Limited time for lengthy financial planning sessions
- Wants transparency in recommendations and costs

**Technology Comfort:** High - uses financial apps, comfortable with digital interfaces

**Preferred Interaction Style:** Self-service with expert backup, visual explanations, mobile-friendly

### Secondary Persona: JPMorgan Client (Mass Affluent)

**Name:** Jennifer Thompson  
**Age:** 38  
**Role:** Marketing Director at a Fortune 500 company  
**Net Worth:** $750K (including home equity and 401k)  

**Background:**
Jennifer is a working professional with a household income of $180K. She has basic financial planning knowledge and uses JPMorgan for banking and some investment services. She has minimal life insurance (2x salary through employer) and is concerned about protecting her family if something happens to her.

**Goals:**
- Ensure adequate protection for her family
- Find affordable life insurance options
- Understand the basics without feeling overwhelmed
- Make decisions that fit her budget
- Plan for her children's education expenses

**Pain Points:**
- Budget constraints for premium payments
- Confusion about term vs. permanent insurance
- Worried about being oversold expensive products
- Limited time for financial planning
- Wants simple, straightforward recommendations

**Technology Comfort:** Moderate to High - uses apps regularly but prefers simple interfaces

**Preferred Interaction Style:** Guided self-service with educational content, cost-conscious



## User Flows for Key Interactions

### User Flow 1: Advisor-Led Needs Assessment

**Scenario:** Sarah (advisor) is meeting with Michael (client) to discuss his overall financial plan and wants to assess his life insurance needs.

**Flow Steps:**
1. **Pre-Meeting Preparation**
   - Sarah logs into the RoboAdvisor platform
   - Reviews Michael's existing portfolio data (imported from JPMorgan systems)
   - Runs a preliminary needs assessment using available client data
   - Prepares talking points and potential recommendations

2. **Client Meeting - Initial Assessment**
   - Sarah shares her screen with the RoboAdvisor interface
   - Together, they review and update Michael's financial information
   - The system asks guided questions about family situation, debts, and goals
   - Real-time calculations show preliminary coverage recommendations

3. **Exploration and Education**
   - Michael asks questions via the chatbot interface
   - The system provides clear explanations of term vs. permanent insurance
   - Interactive visualizations show how different policies would perform
   - Comparison charts display costs and benefits side-by-side

4. **Scenario Planning**
   - They explore "what-if" scenarios (income changes, family growth, etc.)
   - The system adjusts recommendations dynamically
   - Visualizations update to show impact on overall financial plan

5. **Next Steps**
   - Sarah saves the session and recommendations
   - System generates a summary report for Michael to review
   - Follow-up tasks are created in Sarah's CRM system
   - Michael receives access to continue exploring on his own

### User Flow 2: Client Self-Service Discovery

**Scenario:** Jennifer (mass affluent client) wants to explore life insurance options on her own before speaking with an advisor.

**Flow Steps:**
1. **Initial Access**
   - Jennifer accesses the RoboAdvisor through JPMorgan's client portal
   - Simple authentication using existing JPMorgan credentials
   - Brief welcome screen explains the tool's purpose and capabilities

2. **Needs Assessment**
   - Guided questionnaire about her financial situation
   - Progressive disclosure - starts simple, gets more detailed as needed
   - Option to import data from existing JPMorgan accounts (with permission)
   - Clear progress indicators throughout the process

3. **Recommendation Generation**
   - System calculates coverage needs based on her inputs
   - Presents recommendations in order of priority (term first for budget-conscious users)
   - Clear explanations of why each recommendation was made
   - Cost estimates with monthly/annual payment options

4. **Education and Exploration**
   - Interactive chatbot available for questions
   - Educational content library with articles and videos
   - Comparison tools to understand different product types
   - Glossary of insurance terms with simple explanations

5. **Visualization and Planning**
   - Charts showing coverage gaps and recommended solutions
   - Timeline view of how needs might change over time
   - Integration with her existing financial picture from JPMorgan

6. **Action Steps**
   - Option to schedule a call with an advisor
   - Save recommendations for later review
   - Share summary with spouse or family members
   - Begin application process for simple term products

### User Flow 3: Complex Product Illustration

**Scenario:** Sarah needs to explain an Indexed Universal Life (IUL) policy to Michael, showing how it could serve as both protection and a tax-deferred investment vehicle.

**Flow Steps:**
1. **Product Selection**
   - Sarah selects IUL from the product menu
   - System loads Michael's profile and previous assessment data
   - Initial parameters are pre-populated based on his situation

2. **Parameter Configuration**
   - Adjust death benefit amount, premium payment schedule
   - Select index options and participation rates
   - Configure riders (disability waiver, long-term care, etc.)
   - Real-time validation ensures realistic scenarios

3. **Projection Generation**
   - System generates multiple scenarios (conservative, moderate, aggressive)
   - Shows guaranteed vs. non-guaranteed elements clearly
   - Displays cash value growth over time with different market conditions
   - Compares to alternative investment strategies

4. **Interactive Exploration**
   - Michael can adjust parameters and see immediate impact
   - Stress testing shows performance in down markets
   - Tax implications are clearly explained and visualized
   - Comparison with his current investment portfolio

5. **Risk Disclosure and Education**
   - Clear explanation of risks and limitations
   - Regulatory disclosures presented in understandable format
   - Chatbot available for specific questions about product features
   - Links to additional educational resources

6. **Documentation and Next Steps**
   - Detailed illustration report generated
   - Summary of key points and recommendations
   - Action items for both advisor and client
   - Integration with JPMorgan's proposal and application systems


## Design Concept and Visual Direction

### Design Philosophy

The Everly RoboAdvisor interface will embody a design philosophy centered on **trust, clarity, and empowerment**. Given the sensitive nature of financial planning and life insurance decisions, the design must convey professionalism and reliability while remaining approachable and easy to understand. The visual design will balance sophistication appropriate for JPMorgan's brand with the accessibility needed for diverse user groups.

### Visual Style Guidelines

**Color Palette:**
- **Primary Blue:** #1B365D (JPMorgan-inspired navy for trust and stability)
- **Secondary Blue:** #4A90A4 (lighter blue for interactive elements)
- **Accent Green:** #00A651 (for positive indicators, growth, and success states)
- **Warning Orange:** #FF6B35 (for alerts and important information)
- **Neutral Gray:** #F8F9FA (background), #6C757D (text), #DEE2E6 (borders)
- **White:** #FFFFFF (primary background and cards)

**Typography:**
- **Primary Font:** Inter (clean, modern, highly legible)
- **Headings:** Inter Bold (24px-32px for main headings, 18px-20px for subheadings)
- **Body Text:** Inter Regular (16px for primary text, 14px for secondary)
- **Data/Numbers:** Inter Medium (for emphasis on financial figures)

**Visual Elements:**
- **Cards and Containers:** Subtle shadows (0 2px 8px rgba(0,0,0,0.1)) with 8px border radius
- **Icons:** Outline style with 2px stroke weight for consistency
- **Charts and Graphs:** Clean, minimal design with clear data visualization
- **Interactive Elements:** Subtle hover states and smooth transitions (200ms ease)

### Key Interface Components

#### 1. Dashboard Layout
The main dashboard will feature a clean, card-based layout with clear information hierarchy:
- **Header:** Navigation, user profile, and quick actions
- **Main Content Area:** Primary tools and information panels
- **Sidebar:** Navigation menu and contextual information
- **Footer:** Support links and compliance information

#### 2. Needs Assessment Calculator
**Visual Design:**
- **Progress Indicator:** Clear step-by-step progress bar at the top
- **Form Layout:** Single-column layout with grouped related fields
- **Input Styling:** Clean form fields with floating labels and validation states
- **Results Display:** Prominent display of recommendations with supporting visualizations

**Interactive Elements:**
- **Slider Controls:** For adjusting coverage amounts and time periods
- **Toggle Switches:** For yes/no questions and feature selections
- **Dropdown Menus:** For categorical selections (family status, income ranges)
- **Real-time Updates:** Instant calculation updates as users modify inputs

#### 3. Chatbot Interface
**Design Approach:**
- **Conversational Layout:** Chat bubble interface with clear distinction between user and system messages
- **Quick Actions:** Suggested questions and common actions as clickable buttons
- **Rich Responses:** Support for text, images, charts, and interactive elements within chat
- **Typing Indicators:** Visual feedback when the system is processing responses

#### 4. Visualization Components
**Chart Types:**
- **Line Charts:** For showing cash value growth over time
- **Bar Charts:** For comparing different policy options
- **Pie Charts:** For showing portfolio allocation including life insurance
- **Interactive Elements:** Hover states, tooltips, and clickable legends

### Wireframes and Layout Concepts

#### Main Dashboard Wireframe
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo | Navigation | User Profile | Notifications    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │   Quick      │ │  Current    │ │ Recommended │ │ Recent  │ │
│ │   Actions    │ │  Coverage   │ │   Actions   │ │ Activity│ │
│ │             │ │             │ │             │ │         │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────────┐ │
│ │                             │ │                         │ │
│ │     Needs Assessment        │ │    Portfolio Overview  │ │
│ │        Calculator           │ │     with Insurance     │ │
│ │                             │ │                         │ │
│ └─────────────────────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                 AI Assistant / Chatbot                  │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Needs Assessment Flow Wireframe
```
Step 1: Personal Information
┌─────────────────────────────────────────┐
│ Progress: ●●○○○ (Step 2 of 5)            │
├─────────────────────────────────────────┤
│ Personal Details                        │
│ ┌─────────────┐ ┌─────────────┐        │
│ │ Age: [__]   │ │ Income: [$] │        │
│ └─────────────┘ └─────────────┘        │
│                                         │
│ Family Status: [Dropdown ▼]            │
│ Number of Dependents: [Slider ●──]     │
│                                         │
│ [Previous] [Continue →]                 │
└─────────────────────────────────────────┘

Step 5: Results & Recommendations
┌─────────────────────────────────────────┐
│ Your Life Insurance Recommendations     │
├─────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐        │
│ │ Recommended │ │ Current Gap │        │
│ │ Coverage    │ │             │        │
│ │ $750,000    │ │ $500,000    │        │
│ └─────────────┘ └─────────────┘        │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │        Policy Comparison Chart      │ │
│ │    [Term] vs [Permanent] Options    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Explore Options] [Talk to Advisor]     │
└─────────────────────────────────────────┘
```

### Mobile Responsiveness

The design will be fully responsive, adapting to different screen sizes:
- **Desktop (1200px+):** Full dashboard layout with side-by-side components
- **Tablet (768px-1199px):** Stacked layout with collapsible sidebar
- **Mobile (320px-767px):** Single-column layout with bottom navigation

### Accessibility Considerations

- **WCAG 2.1 AA Compliance:** All color contrasts, font sizes, and interactive elements will meet accessibility standards
- **Keyboard Navigation:** Full keyboard accessibility for all interactive elements
- **Screen Reader Support:** Proper ARIA labels and semantic HTML structure
- **Focus Indicators:** Clear visual focus indicators for keyboard navigation
- **Alternative Text:** Descriptive alt text for all images and charts


## Design Principles and Branding Guidelines

### Core Design Principles

#### 1. Trust Through Transparency
Every design decision should reinforce trust and credibility. This means:
- **Clear Information Hierarchy:** Important information is prominently displayed and easy to find
- **Honest Communication:** No hidden fees or misleading information; all assumptions and calculations are clearly explained
- **Professional Aesthetics:** Clean, polished design that reflects the quality and reliability of JPMorgan and Everly
- **Data Security Indicators:** Visible security badges and encryption indicators to reassure users about data protection

#### 2. Simplicity Without Sacrificing Depth
The interface should be approachable for novices while providing depth for experts:
- **Progressive Disclosure:** Start with simple concepts and allow users to drill down into details as needed
- **Contextual Help:** Tooltips, explanations, and educational content available when and where users need it
- **Customizable Complexity:** Allow advisors to access more detailed tools while keeping client-facing interfaces simple
- **Clear Visual Hierarchy:** Use typography, color, and spacing to guide users through complex information

#### 3. Empowerment Through Education
The design should educate users and build their confidence in making financial decisions:
- **Visual Learning:** Charts, graphs, and illustrations to make complex concepts understandable
- **Interactive Exploration:** Allow users to experiment with different scenarios and see immediate results
- **Guided Discovery:** Lead users through logical decision-making processes rather than overwhelming them with options
- **Knowledge Building:** Provide educational resources and explanations that build financial literacy

#### 4. Efficiency for Professionals
For advisor users, the interface should enhance productivity and effectiveness:
- **Workflow Optimization:** Streamlined processes that reduce time spent on routine tasks
- **Quick Access:** Frequently used tools and information readily available
- **Multi-tasking Support:** Ability to work with multiple clients or scenarios simultaneously
- **Integration Readiness:** Seamless connection with existing JPMorgan tools and workflows

### Branding Guidelines

#### JPMorgan Brand Integration
The design will respectfully incorporate JPMorgan's brand elements while maintaining Everly's identity:

**Color Harmony:**
- Primary use of JPMorgan's signature blue (#1B365D) for trust and authority
- Everly's brand colors as accents and secondary elements
- Neutral palette to ensure readability and professional appearance

**Typography Consistency:**
- Align with JPMorgan's typography standards where possible
- Maintain readability and accessibility across all text elements
- Use consistent font weights and sizes for information hierarchy

**Logo and Branding:**
- Co-branding approach with both JPMorgan and Everly logos appropriately placed
- "Powered by Everly" attribution in footer or appropriate location
- Consistent brand messaging that reinforces the partnership value

#### Visual Identity Elements

**Iconography:**
- Custom icon set that aligns with both brands' visual languages
- Consistent style (outline, filled, or mixed) across all interface elements
- Financial and insurance-specific icons that are immediately recognizable
- Scalable vector icons that work across all device sizes

**Photography and Illustrations:**
- Professional, diverse imagery that reflects JPMorgan's client base
- Custom illustrations for complex financial concepts
- Consistent style and color treatment across all visual elements
- Avoid stock photography clichés; focus on authentic, relatable imagery

**Data Visualization Style:**
- Clean, modern chart designs with consistent color coding
- Clear labeling and legends for all data visualizations
- Interactive elements that enhance understanding without overwhelming
- Consistent styling across all chart types and data displays

### User Experience Principles

#### Advisor Experience Optimization
**Confidence Building:**
- Provide clear explanations and rationale for all recommendations
- Include risk assessments and compliance information
- Offer multiple scenarios and comparison tools
- Enable easy customization of presentations for different client types

**Efficiency Enhancement:**
- Pre-populate forms with available client data
- Provide templates and shortcuts for common scenarios
- Enable quick switching between different calculation modes
- Integrate with existing CRM and planning tools

**Professional Presentation:**
- Generate client-ready reports and presentations
- Provide talking points and explanation guides
- Enable screen sharing and collaborative exploration
- Maintain professional appearance in all client-facing materials

#### Client Experience Optimization
**Accessibility and Inclusion:**
- Support for multiple languages where appropriate
- Accommodations for users with disabilities
- Clear, jargon-free language with definitions available
- Flexible interface that adapts to user preferences and needs

**Engagement and Understanding:**
- Interactive elements that encourage exploration
- Visual feedback for all user actions
- Clear progress indicators for multi-step processes
- Immediate validation and helpful error messages

**Trust and Comfort:**
- Transparent data usage and privacy policies
- Clear explanation of how recommendations are generated
- Option to save progress and return later
- Easy access to human support when needed

### Implementation Guidelines

#### Development Standards
**Code Quality:**
- Semantic HTML structure for accessibility
- CSS-in-JS or styled-components for maintainable styling
- Responsive design using mobile-first approach
- Performance optimization for fast loading times

**Testing Requirements:**
- Cross-browser compatibility testing
- Mobile device testing across different screen sizes
- Accessibility testing with screen readers and keyboard navigation
- User testing with both advisor and client personas

**Maintenance Considerations:**
- Modular component architecture for easy updates
- Consistent naming conventions and documentation
- Version control for design assets and components
- Regular design system updates and maintenance

This comprehensive design approach ensures that the Everly RoboAdvisor will not only meet the functional requirements but also provide an exceptional user experience that builds trust, enhances understanding, and empowers both advisors and clients to make informed life insurance decisions.

