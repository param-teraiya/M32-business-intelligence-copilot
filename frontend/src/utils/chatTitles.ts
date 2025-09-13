/**
 * Smart chat title generation utilities
 * Generates meaningful titles based on conversation content, similar to ChatGPT
 */

// Predefined title templates based on business intelligence patterns
const titleTemplates = {
  market_research: [
    "Market Analysis",
    "Industry Research", 
    "Market Trends",
    "Market Insights",
    "Industry Overview"
  ],
  competitor_analysis: [
    "Competitor Analysis",
    "Competitive Intelligence",
    "Competition Research",
    "Market Competition",
    "Competitor Insights"
  ],
  business_strategy: [
    "Business Strategy",
    "Strategic Planning",
    "Growth Strategy",
    "Business Planning",
    "Strategic Analysis"
  ],
  general_business: [
    "Business Discussion",
    "Business Consultation",
    "Strategic Advice",
    "Business Insights",
    "Business Planning"
  ],
  industry_specific: {
    technology: ["Tech Strategy", "Technology Analysis", "Tech Market Research"],
    healthcare: ["Healthcare Strategy", "Medical Industry Analysis", "Healthcare Insights"],
    finance: ["Financial Strategy", "Fintech Analysis", "Financial Planning"],
    retail: ["Retail Strategy", "E-commerce Analysis", "Retail Insights"],
    manufacturing: ["Manufacturing Strategy", "Industrial Analysis", "Production Planning"],
    education: ["EdTech Strategy", "Education Analysis", "Learning Solutions"],
    consulting: ["Consulting Strategy", "Professional Services", "Advisory Planning"]
  }
}

// Keywords that help identify the type of conversation
const keywordPatterns = {
  market_research: [
    'market', 'industry', 'trends', 'research', 'analysis', 'size', 'growth', 'forecast',
    'market share', 'market size', 'industry trends', 'market analysis'
  ],
  competitor_analysis: [
    'competitor', 'competition', 'competitive', 'rival', 'vs', 'compare', 'comparison',
    'market leader', 'competitive advantage', 'swot', 'benchmark'
  ],
  business_strategy: [
    'strategy', 'strategic', 'plan', 'planning', 'growth', 'expansion', 'business model',
    'revenue', 'profit', 'scale', 'scaling', 'go-to-market', 'gtm'
  ],
  startup: [
    'startup', 'launch', 'mvp', 'product-market fit', 'funding', 'venture', 'seed',
    'series a', 'pitch', 'investor'
  ],
  marketing: [
    'marketing', 'brand', 'branding', 'campaign', 'advertising', 'promotion',
    'customer acquisition', 'lead generation', 'conversion'
  ]
}

// Extract key topics from user message
function extractTopics(message: string): string[] {
  const topics = []
  const lowerMessage = message.toLowerCase()
  
  // Look for specific business topics
  if (lowerMessage.includes('market') || lowerMessage.includes('industry')) {
    topics.push('market_research')
  }
  if (lowerMessage.includes('competitor') || lowerMessage.includes('competition')) {
    topics.push('competitor_analysis')
  }
  if (lowerMessage.includes('strategy') || lowerMessage.includes('plan')) {
    topics.push('business_strategy')
  }
  if (lowerMessage.includes('startup') || lowerMessage.includes('launch')) {
    topics.push('startup')
  }
  if (lowerMessage.includes('marketing') || lowerMessage.includes('brand')) {
    topics.push('marketing')
  }
  
  return topics
}

// Extract industry from message or business context
function extractIndustry(message: string, businessContext?: any): string | null {
  const lowerMessage = message.toLowerCase()
  const industries = [
    'technology', 'tech', 'software', 'saas',
    'healthcare', 'medical', 'health',
    'finance', 'financial', 'fintech', 'banking',
    'retail', 'e-commerce', 'ecommerce',
    'manufacturing', 'industrial',
    'education', 'edtech',
    'consulting', 'professional services',
    'real estate', 'construction',
    'hospitality', 'travel',
    'energy', 'renewable'
  ]
  
  // Check business context first
  if (businessContext?.industry) {
    return businessContext.industry.toLowerCase()
  }
  
  // Look for industry keywords in message
  for (const industry of industries) {
    if (lowerMessage.includes(industry)) {
      if (industry === 'tech' || industry === 'software' || industry === 'saas') {
        return 'technology'
      }
      if (industry === 'medical' || industry === 'health') {
        return 'healthcare'
      }
      if (industry === 'financial' || industry === 'fintech' || industry === 'banking') {
        return 'finance'
      }
      if (industry === 'e-commerce' || industry === 'ecommerce') {
        return 'retail'
      }
      if (industry === 'industrial') {
        return 'manufacturing'
      }
      if (industry === 'edtech') {
        return 'education'
      }
      if (industry === 'professional services') {
        return 'consulting'
      }
      return industry
    }
  }
  
  return null
}

// Generate smart title based on first user message
export function generateSmartChatTitle(
  firstMessage: string, 
  businessContext?: any
): string {
  const topics = extractTopics(firstMessage)
  const industry = extractIndustry(firstMessage, businessContext)
  
  // If we have industry-specific templates and detected industry
  if (industry && titleTemplates.industry_specific[industry as keyof typeof titleTemplates.industry_specific]) {
    const industryTemplates = titleTemplates.industry_specific[industry as keyof typeof titleTemplates.industry_specific]
    return industryTemplates[Math.floor(Math.random() * industryTemplates.length)]
  }
  
  // Use topic-based templates
  if (topics.length > 0) {
    const primaryTopic = topics[0]
    const templates = titleTemplates[primaryTopic as keyof typeof titleTemplates]
    if (Array.isArray(templates)) {
      return templates[Math.floor(Math.random() * templates.length)]
    }
  }
  
  // Try to extract company/product names for more specific titles
  const companyMatch = firstMessage.match(/\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b/g)
  if (companyMatch && companyMatch.length > 0) {
    const companyName = companyMatch[0]
    if (topics.includes('competitor_analysis')) {
      return `${companyName} Analysis`
    }
    if (topics.includes('market_research')) {
      return `${companyName} Market Research`
    }
    return `${companyName} Strategy`
  }
  
  // Fallback to general business templates
  const generalTemplates = titleTemplates.general_business
  return generalTemplates[Math.floor(Math.random() * generalTemplates.length)]
}

// Generate title based on message content patterns
export function generateTitleFromContent(message: string): string {
  const lowerMessage = message.toLowerCase()
  
  // Specific question patterns
  if (lowerMessage.includes('what') && lowerMessage.includes('trend')) {
    return "Market Trends Analysis"
  }
  if (lowerMessage.includes('who') && lowerMessage.includes('competitor')) {
    return "Competitor Identification"
  }
  if (lowerMessage.includes('how') && lowerMessage.includes('grow')) {
    return "Growth Strategy"
  }
  if (lowerMessage.includes('analyze') && lowerMessage.includes('market')) {
    return "Market Analysis"
  }
  if (lowerMessage.includes('business plan')) {
    return "Business Planning"
  }
  if (lowerMessage.includes('go-to-market') || lowerMessage.includes('gtm')) {
    return "Go-to-Market Strategy"
  }
  if (lowerMessage.includes('pricing')) {
    return "Pricing Strategy"
  }
  if (lowerMessage.includes('customer')) {
    return "Customer Strategy"
  }
  if (lowerMessage.includes('revenue')) {
    return "Revenue Strategy"
  }
  if (lowerMessage.includes('funding') || lowerMessage.includes('investment')) {
    return "Funding Strategy"
  }
  
  // Extract first few meaningful words as title
  const words = message.split(' ').filter(word => 
    word.length > 3 && 
    !['what', 'how', 'when', 'where', 'why', 'the', 'and', 'but', 'for', 'with'].includes(word.toLowerCase())
  )
  
  if (words.length >= 2) {
    const title = words.slice(0, 3).join(' ')
    return title.charAt(0).toUpperCase() + title.slice(1)
  }
  
  // Final fallback
  return generateSmartChatTitle(message)
}

// List of creative chat title starters (like ChatGPT)
export const creativeTitles = [
  "Business Insights Session",
  "Strategic Planning Chat", 
  "Market Intelligence Brief",
  "Competitive Analysis Deep Dive",
  "Growth Strategy Workshop",
  "Business Intelligence Consultation",
  "Strategic Advisory Session",
  "Market Research Discussion",
  "Business Development Chat",
  "Innovation Strategy Talk",
  "Digital Transformation Planning",
  "Revenue Optimization Session",
  "Customer Strategy Workshop",
  "Operational Excellence Planning",
  "Investment Strategy Discussion"
]

// Get a random creative title
export function getRandomCreativeTitle(): string {
  return creativeTitles[Math.floor(Math.random() * creativeTitles.length)]
}
