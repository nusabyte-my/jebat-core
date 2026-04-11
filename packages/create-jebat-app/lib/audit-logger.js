const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const homeDir = os.homedir();
const logDir = path.join(homeDir, '.jebat', 'logs');
const auditLogFile = path.join(logDir, 'audit.log');

class AuditLogger {
  constructor(options = {}) {
    this.enabled = options.enabled !== false;
    this.level = options.level || 'info'; // debug, info, warn, error
    this.includeInput = options.includeInput || false;
    this.includeOutput = options.includeOutput !== false;
    this.tamperEvident = options.tamperEvident !== false;
    this.maxFileSize = options.maxFileSize || 100 * 1024 * 1024; // 100MB
    this.logChain = [];
    
    if (this.enabled) {
      this.initialize();
    }
  }

  async initialize() {
    await fs.ensureDir(logDir);
    
    // Check file size and rotate if needed
    if (await fs.pathExists(auditLogFile)) {
      const stats = await fs.stat(auditLogFile);
      if (stats.size > this.maxFileSize) {
        await this.rotateLogs();
      }
    }
    
    // Write log header
    if (!(await fs.pathExists(auditLogFile))) {
      await this.writeHeader();
    }
  }

  async writeHeader() {
    const header = {
      timestamp: new Date().toISOString(),
      version: '2.0.0',
      hostname: os.hostname(),
      userId: process.env.USER || os.userInfo().username,
      securityLevel: process.env.JEBAT_SECURITY_LEVEL || 'enterprise',
      tamperEvident: this.tamperEvident
    };
    
    const logEntry = this.formatEntry('SYSTEM', 'AUDIT_LOG_INITIALIZED', header);
    await this.writeToFile(logEntry);
  }

  async log(category, action, data = {}) {
    if (!this.enabled) return;
    
    const entry = {
      timestamp: new Date().toISOString(),
      category,
      action,
      data: this.sanitizeData(data),
      hash: null
    };
    
    // Generate hash for tamper evidence
    if (this.tamperEvident) {
      const previousHash = this.logChain.length > 0 
        ? this.logChain[this.logChain.length - 1]
        : '0000000000000000';
      
      const content = JSON.stringify(entry) + previousHash;
      entry.hash = crypto.createHash('sha256').update(content).digest('hex');
      this.logChain.push(entry.hash);
    }
    
    const logEntry = this.formatEntry(category, action, entry);
    await this.writeToFile(logEntry);
  }

  async logRequest(requestData) {
    const sanitized = {
      method: requestData.method,
      path: requestData.path,
      userAgent: requestData.userAgent,
      sessionId: requestData.sessionId,
      inputLength: requestData.input?.length || 0,
      timestamp: new Date().toISOString()
    };
    
    if (this.includeInput && requestData.input) {
      sanitized.inputPreview = requestData.input.substring(0, 200);
    }
    
    await this.log('REQUEST', 'RECEIVED', sanitized);
  }

  async logResponse(responseData) {
    const sanitized = {
      statusCode: responseData.statusCode,
      duration: responseData.duration,
      outputLength: responseData.output?.length || 0
    };
    
    if (this.includeOutput && responseData.output) {
      sanitized.outputPreview = responseData.output.substring(0, 200);
    }
    
    await this.log('RESPONSE', 'SENT', sanitized);
  }

  async logCommand(commandData) {
    const sanitized = {
      command: commandData.command,
      args: commandData.args || [],
      workingDirectory: commandData.cwd,
      timeout: commandData.timeout,
      userId: commandData.userId
    };
    
    await this.log('COMMAND', 'EXECUTED', sanitized);
  }

  async logSecurity(event, details) {
    await this.log('SECURITY', event, details);
  }

  async logError(error, context = {}) {
    const sanitized = {
      message: error.message,
      stack: error.stack,
      context: this.sanitizeData(context)
    };
    
    await this.log('ERROR', 'OCCURRED', sanitized);
  }

  sanitizeData(data) {
    const sanitized = { ...data };
    
    // Remove common secret patterns
    const secretPatterns = [
      /api[_-]?key['"]?\s*[:=]\s*['"]?([^'"]+)['"]?/gi,
      /token['"]?\s*[:=]\s*['"]?([^'"]+)['"]?/gi,
      /secret['"]?\s*[:=]\s*['"]?([^'"]+)['"]?/gi,
      /password['"]?\s*[:=]\s*['"]?([^'"]+)['"]?/gi,
      /sk-[a-zA-Z0-9]{20,}/g,
      /ghp_[a-zA-Z0-9]{20,}/g,
      /xoxb-[a-zA-Z0-9-]+/g
    ];
    
    for (const [key, value] of Object.entries(sanitized)) {
      if (typeof value === 'string') {
        for (const pattern of secretPatterns) {
          sanitized[key] = value.replace(pattern, '$1[REDACTED]');
        }
      }
    }
    
    return sanitized;
  }

  formatEntry(category, action, data) {
    return JSON.stringify({
      ...data,
      category,
      action
    });
  }

  async writeToFile(logEntry) {
    try {
      await fs.appendFile(auditLogFile, logEntry + '\n');
    } catch (error) {
      console.error('Failed to write audit log:', error.message);
    }
  }

  async rotateLogs() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const rotatedFile = path.join(logDir, `audit-${timestamp}.log`);
    
    try {
      await fs.move(auditLogFile, rotatedFile);
      await this.writeHeader();
    } catch (error) {
      console.error('Failed to rotate logs:', error.message);
    }
  }

  async getLogs(options = {}) {
    if (!(await fs.pathExists(auditLogFile))) {
      return [];
    }
    
    const content = await fs.readFile(auditLogFile, 'utf8');
    const lines = content.trim().split('\n');
    
    let logs = lines.map(line => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    }).filter(Boolean);
    
    // Filter by category if specified
    if (options.category) {
      logs = logs.filter(log => log.category === options.category);
    }
    
    // Filter by action if specified
    if (options.action) {
      logs = logs.filter(log => log.action === options.action);
    }
    
    // Limit results
    if (options.limit) {
      logs = logs.slice(-options.limit);
    }
    
    return logs;
  }

  async verifyIntegrity() {
    if (!(await fs.pathExists(auditLogFile))) {
      return { valid: false, reason: 'No log file found' };
    }
    
    const content = await fs.readFile(auditLogFile, 'utf8');
    const lines = content.trim().split('\n');
    
    let previousHash = '0000000000000000';
    let valid = true;
    let invalidLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      try {
        const entry = JSON.parse(lines[i]);
        
        if (entry.hash) {
          const expectedContent = JSON.stringify({
            timestamp: entry.timestamp,
            category: entry.category,
            action: entry.action,
            ...entry.data,
            hash: null
          }) + previousHash;
          
          const expectedHash = crypto.createHash('sha256')
            .update(expectedContent)
            .digest('hex');
          
          if (entry.hash !== expectedHash) {
            valid = false;
            invalidLines.push(i + 1);
          }
          
          previousHash = entry.hash;
        }
      } catch {
        valid = false;
        invalidLines.push(i + 1);
      }
    }
    
    return {
      valid,
      totalLines: lines.length,
      invalidLines: invalidLines.length > 0 ? invalidLines : undefined
    };
  }
}

// Export singleton instance
let auditLoggerInstance = null;

function getAuditLogger(options) {
  if (!auditLoggerInstance) {
    auditLoggerInstance = new AuditLogger(options);
  }
  return auditLoggerInstance;
}

module.exports = { AuditLogger, getAuditLogger };
