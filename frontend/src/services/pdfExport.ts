import { ChatSession, ChatMessage } from './chat';

interface PDFExportOptions {
  includeTimestamps?: boolean;
  includeMetadata?: boolean;
  includeRecommendations?: boolean;
  includeCharts?: boolean;
  template?: 'conversation' | 'advice_summary' | 'detailed_report';
}

class PDFExportService {
  // Export conversation as PDF
  async exportConversation(
    session: ChatSession, 
    options: PDFExportOptions = {}
  ): Promise<void> {
    const {
      includeTimestamps = true,
      includeMetadata = true,
      includeRecommendations = true,
      includeCharts = false,
      template = 'conversation'
    } = options;

    try {
      // For client-side PDF generation, we'll use HTML and print CSS
      const htmlContent = this.generateHTMLContent(session, options);
      
      // Create a new window for PDF generation
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        throw new Error('Could not open print window. Please check popup blockers.');
      }

      printWindow.document.write(htmlContent);
      printWindow.document.close();
      
      // Wait for content to load and then trigger print
      printWindow.onload = () => {
        setTimeout(() => {
          printWindow.print();
          setTimeout(() => {
            printWindow.close();
          }, 1000);
        }, 500);
      };
    } catch (error) {
      console.error('Failed to export PDF:', error);
      throw error;
    }
  }

  // Generate structured HTML content for PDF
  private generateHTMLContent(
    session: ChatSession, 
    options: PDFExportOptions
  ): string {
    const { includeTimestamps, includeMetadata, includeRecommendations } = options;
    
    const messages = session.messages || [];
    const recommendations = this.extractRecommendations(messages);
    const summary = this.generateSummary(session);
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${session.title} - Financial Planning Advice</title>
    <style>
        ${this.getPrintCSS()}
    </style>
</head>
<body>
    <div class="document">
        <!-- Header -->
        <header class="header">
            <div class="header-content">
                <h1 class="title">${session.title}</h1>
                <div class="document-info">
                    <p><strong>Generated:</strong> ${new Date().toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</p>
                    <p><strong>Conversation Date:</strong> ${new Date(session.createdAt).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric'
                    })}</p>
                    <p><strong>Total Messages:</strong> ${messages.length}</p>
                </div>
            </div>
            <div class="brand">
                <h3>AI Financial Advisor</h3>
                <p>Personalized Financial Planning Platform</p>
            </div>
        </header>

        <!-- Executive Summary -->
        <section class="section">
            <h2>Executive Summary</h2>
            <div class="summary-content">
                ${summary}
            </div>
        </section>

        <!-- Key Recommendations (if available) -->
        ${includeRecommendations && recommendations.length > 0 ? `
        <section class="section recommendations">
            <h2>Key Recommendations</h2>
            <div class="recommendations-list">
                ${recommendations.map((rec, index) => `
                    <div class="recommendation-item">
                        <div class="recommendation-header">
                            <h4>${rec.title}</h4>
                            <span class="priority ${rec.priority}">${rec.priority.toUpperCase()}</span>
                        </div>
                        <p class="recommendation-description">${rec.description}</p>
                        ${rec.impact ? `<p class="recommendation-impact"><strong>Expected Impact:</strong> ${rec.impact}</p>` : ''}
                    </div>
                `).join('')}
            </div>
        </section>` : ''}

        <!-- Conversation Transcript -->
        <section class="section conversation">
            <h2>Conversation Transcript</h2>
            <div class="messages">
                ${messages.map((message, index) => `
                    <div class="message ${message.role}">
                        <div class="message-header">
                            <div class="message-role">
                                <span class="role-badge ${message.role}">
                                    ${message.role === 'user' ? '👤 You' : '🤖 AI Advisor'}
                                </span>
                            </div>
                            ${includeTimestamps ? `
                                <div class="message-time">
                                    ${new Date(message.timestamp).toLocaleString()}
                                </div>
                            ` : ''}
                        </div>
                        <div class="message-content">
                            ${this.formatMessageContent(message.content)}
                        </div>
                        ${includeMetadata && message.metadata?.confidence ? `
                            <div class="message-metadata">
                                <small>Confidence: ${Math.round(message.metadata.confidence * 100)}%</small>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        </section>

        <!-- Footer -->
        <footer class="footer">
            <div class="disclaimer">
                <h4>Important Disclaimer</h4>
                <p>
                    This document contains AI-generated financial advice based on the information provided 
                    during your conversation. This advice is for informational purposes only and should not 
                    be considered as professional financial advice. Please consult with a qualified financial 
                    advisor before making any investment decisions.
                </p>
            </div>
            <div class="footer-info">
                <p>Generated by AI Financial Advisor - ${window.location.hostname}</p>
                <p>Document ID: ${session.id}</p>
            </div>
        </footer>
    </div>
</body>
</html>`;
  }

  // Extract recommendations from messages
  private extractRecommendations(messages: ChatMessage[]): Array<{
    title: string;
    description: string;
    priority: string;
    impact?: string;
  }> {
    const recommendations: Array<{
      title: string;
      description: string;
      priority: string;
      impact?: string;
    }> = [];
    
    messages.forEach(message => {
      if (message.role === 'assistant' && message.metadata?.suggestions) {
        message.metadata.suggestions.forEach(suggestion => {
          recommendations.push({
            title: suggestion,
            description: `Based on our conversation, this recommendation was generated.`,
            priority: 'medium',
            impact: 'Moderate'
          });
        });
      }
      
      // Look for recommendation keywords in content
      const content = message.content.toLowerCase();
      if (message.role === 'assistant' && 
          (content.includes('recommend') || content.includes('suggest') || content.includes('should'))) {
        
        const sentences = message.content.split('.').filter(s => s.trim());
        sentences.forEach(sentence => {
          if (sentence.toLowerCase().includes('recommend') || 
              sentence.toLowerCase().includes('suggest') ||
              sentence.toLowerCase().includes('should')) {
            recommendations.push({
              title: sentence.trim().substring(0, 100) + (sentence.length > 100 ? '...' : ''),
              description: sentence.trim(),
              priority: 'medium'
            });
          }
        });
      }
    });
    
    // Remove duplicates and limit to top 10
    const uniqueRecommendations = recommendations.filter((rec, index, arr) => 
      arr.findIndex(r => r.title === rec.title) === index
    ).slice(0, 10);
    
    return uniqueRecommendations;
  }

  // Generate conversation summary
  private generateSummary(session: ChatSession): string {
    const messages = session.messages || [];
    const userMessages = messages.filter(m => m.role === 'user');
    const aiMessages = messages.filter(m => m.role === 'assistant');
    
    // Extract topics discussed
    const topics = new Set<string>();
    messages.forEach(message => {
      const content = message.content.toLowerCase();
      if (content.includes('portfolio') || content.includes('investment')) topics.add('Portfolio Management');
      if (content.includes('retirement')) topics.add('Retirement Planning');
      if (content.includes('tax')) topics.add('Tax Strategy');
      if (content.includes('budget') || content.includes('spending')) topics.add('Budgeting');
      if (content.includes('insurance')) topics.add('Insurance');
      if (content.includes('debt')) topics.add('Debt Management');
      if (content.includes('savings')) topics.add('Savings Strategy');
      if (content.includes('goal')) topics.add('Financial Goals');
    });
    
    return `
      <div class="summary-stats">
        <div class="stat">
          <strong>Conversation Length:</strong> ${messages.length} messages
        </div>
        <div class="stat">
          <strong>Duration:</strong> ${this.calculateConversationDuration(session)}
        </div>
        <div class="stat">
          <strong>Topics Discussed:</strong> ${Array.from(topics).join(', ') || 'General Financial Planning'}
        </div>
      </div>
      <p>
        This conversation covered various aspects of financial planning, with a focus on 
        personalized advice and actionable recommendations. The AI advisor provided 
        insights based on your specific financial situation and goals.
      </p>
    `;
  }

  // Calculate conversation duration
  private calculateConversationDuration(session: ChatSession): string {
    const messages = session.messages || [];
    if (messages.length < 2) return 'Less than 1 minute';
    
    const firstMessage = new Date(messages[0].timestamp);
    const lastMessage = new Date(messages[messages.length - 1].timestamp);
    const diffMs = lastMessage.getTime() - firstMessage.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 60) return `${diffMins} minutes`;
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return `${hours}h ${mins}m`;
  }

  // Format message content for PDF
  private formatMessageContent(content: string): string {
    // Convert markdown-like formatting to HTML
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
    
    // Handle lists
    formatted = formatted.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return formatted;
  }

  // Get CSS styles for PDF printing
  private getPrintCSS(): string {
    return `
      @page {
        margin: 1in;
        size: letter;
      }
      
      * {
        box-sizing: border-box;
      }
      
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        background: white;
        margin: 0;
        padding: 0;
      }
      
      .document {
        max-width: 100%;
        margin: 0 auto;
      }
      
      .header {
        border-bottom: 3px solid #2563eb;
        padding-bottom: 20px;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
      }
      
      .header-content .title {
        font-size: 28px;
        font-weight: bold;
        color: #1e40af;
        margin: 0 0 10px 0;
      }
      
      .document-info p {
        margin: 5px 0;
        font-size: 14px;
      }
      
      .brand {
        text-align: right;
      }
      
      .brand h3 {
        margin: 0;
        font-size: 20px;
        color: #2563eb;
      }
      
      .brand p {
        margin: 5px 0 0 0;
        font-size: 12px;
        color: #666;
      }
      
      .section {
        margin-bottom: 40px;
        page-break-inside: avoid;
      }
      
      .section h2 {
        font-size: 22px;
        color: #1e40af;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 10px;
        margin-bottom: 20px;
      }
      
      .summary-stats {
        background: #f8fafc;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
      }
      
      .stat {
        margin-bottom: 10px;
        font-size: 14px;
      }
      
      .recommendations-list {
        space-y: 20px;
      }
      
      .recommendation-item {
        background: #fefefe;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        page-break-inside: avoid;
      }
      
      .recommendation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }
      
      .recommendation-header h4 {
        margin: 0;
        font-size: 16px;
        color: #1e40af;
      }
      
      .priority {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
      }
      
      .priority.high {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
      }
      
      .priority.medium {
        background: #fffbeb;
        color: #d97706;
        border: 1px solid #fed7aa;
      }
      
      .priority.low {
        background: #f0fdf4;
        color: #16a34a;
        border: 1px solid #bbf7d0;
      }
      
      .messages {
        space-y: 25px;
      }
      
      .message {
        margin-bottom: 25px;
        page-break-inside: avoid;
      }
      
      .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }
      
      .role-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
      }
      
      .role-badge.user {
        background: #dbeafe;
        color: #1e40af;
      }
      
      .role-badge.assistant {
        background: #dcfce7;
        color: #16a34a;
      }
      
      .message-time {
        font-size: 12px;
        color: #666;
      }
      
      .message-content {
        background: #f8fafc;
        padding: 15px 20px;
        border-radius: 8px;
        border-left: 4px solid #e5e7eb;
      }
      
      .message.user .message-content {
        border-left-color: #2563eb;
      }
      
      .message.assistant .message-content {
        border-left-color: #16a34a;
      }
      
      .message-metadata {
        margin-top: 8px;
        font-size: 12px;
        color: #666;
      }
      
      .footer {
        border-top: 2px solid #e5e7eb;
        padding-top: 20px;
        margin-top: 40px;
      }
      
      .disclaimer {
        background: #fefce8;
        border: 1px solid #eab308;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
      }
      
      .disclaimer h4 {
        margin: 0 0 10px 0;
        color: #a16207;
      }
      
      .disclaimer p {
        margin: 0;
        font-size: 14px;
        color: #713f12;
      }
      
      .footer-info {
        text-align: center;
        font-size: 12px;
        color: #666;
      }
      
      .footer-info p {
        margin: 5px 0;
      }
      
      code {
        background: #f1f5f9;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 90%;
      }
      
      ul {
        margin: 10px 0;
        padding-left: 20px;
      }
      
      li {
        margin-bottom: 5px;
      }
      
      strong {
        color: #1e40af;
      }
      
      @media print {
        body {
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        
        .section {
          page-break-inside: avoid;
        }
        
        .recommendation-item {
          page-break-inside: avoid;
        }
        
        .message {
          page-break-inside: avoid;
        }
      }
    `;
  }

  // Export advice summary as structured data
  async exportAdviceSummary(session: ChatSession): Promise<string> {
    const recommendations = this.extractRecommendations(session.messages || []);
    const summary = {
      sessionId: session.id,
      title: session.title,
      generatedAt: new Date().toISOString(),
      conversationDate: session.createdAt,
      messageCount: session.messages?.length || 0,
      recommendations: recommendations,
      keyTopics: this.extractTopics(session.messages || []),
      summary: 'AI-generated financial planning conversation with personalized recommendations'
    };
    
    return JSON.stringify(summary, null, 2);
  }

  private extractTopics(messages: ChatMessage[]): string[] {
    const topics = new Set<string>();
    messages.forEach(message => {
      const content = message.content.toLowerCase();
      if (content.includes('portfolio') || content.includes('investment')) topics.add('Portfolio Management');
      if (content.includes('retirement')) topics.add('Retirement Planning');
      if (content.includes('tax')) topics.add('Tax Strategy');
      if (content.includes('budget') || content.includes('spending')) topics.add('Budgeting');
      if (content.includes('insurance')) topics.add('Insurance');
      if (content.includes('debt')) topics.add('Debt Management');
      if (content.includes('savings')) topics.add('Savings Strategy');
      if (content.includes('goal')) topics.add('Financial Goals');
    });
    return Array.from(topics);
  }
}

export const pdfExportService = new PDFExportService();
export default pdfExportService;