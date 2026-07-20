#!/usr/bin/env node

/**
 * Vercel Configuration Validator
 * 
 * This script validates the Vercel deployment configuration
 * and environment setup before deployment.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Vercel Configuration...\n');

const errors = [];
const warnings = [];
const success = [];

// Check if vercel.json exists
const vercelConfigPath = path.join(process.cwd(), 'vercel.json');
if (fs.existsSync(vercelConfigPath)) {
    success.push('✅ vercel.json found');
    
    try {
        const config = JSON.parse(fs.readFileSync(vercelConfigPath, 'utf8'));
        
        // Validate required fields
        if (config.buildCommand) {
            success.push('✅ Build command configured');
        } else {
            warnings.push('⚠️  Build command not specified');
        }
        
        if (config.outputDirectory) {
            success.push('✅ Output directory configured');
        } else {
            errors.push('❌ Output directory not specified');
        }
        
        // Check if output directory exists
        const outputDir = path.join(process.cwd(), config.outputDirectory || 'frontend/dist');
        if (fs.existsSync(outputDir)) {
            success.push('✅ Output directory exists');
        } else {
            warnings.push('⚠️  Output directory does not exist (run build first)');
        }
        
        // Validate headers
        if (config.headers && config.headers.length > 0) {
            success.push('✅ Security headers configured');
        } else {
            warnings.push('⚠️  No security headers configured');
        }
        
        // Validate rewrites for SPA
        if (config.rewrites && config.rewrites.length > 0) {
            success.push('✅ SPA routing rewrites configured');
        } else {
            errors.push('❌ SPA routing rewrites not configured');
        }
        
    } catch (parseError) {
        errors.push('❌ vercel.json is not valid JSON');
    }
} else {
    errors.push('❌ vercel.json not found');
}

// Check frontend package.json
const frontendPackagePath = path.join(process.cwd(), 'frontend', 'package.json');
if (fs.existsSync(frontendPackagePath)) {
    success.push('✅ Frontend package.json found');
    
    try {
        const pkg = JSON.parse(fs.readFileSync(frontendPackagePath, 'utf8'));
        
        if (pkg.scripts && pkg.scripts.build) {
            success.push('✅ Build script available');
        } else {
            errors.push('❌ Build script not found in frontend package.json');
        }
        
        if (pkg.scripts && pkg.scripts.preview) {
            success.push('✅ Preview script available');
        } else {
            warnings.push('⚠️  Preview script not found (optional)');
        }
        
    } catch (parseError) {
        errors.push('❌ Frontend package.json is not valid JSON');
    }
} else {
    errors.push('❌ Frontend package.json not found');
}

// Check environment files
const envFiles = [
    'frontend/.env.production',
    'frontend/.env'
];

envFiles.forEach(envFile => {
    const envPath = path.join(process.cwd(), envFile);
    if (fs.existsSync(envPath)) {
        success.push(`✅ ${envFile} found`);
        
        const content = fs.readFileSync(envPath, 'utf8');
        
        // Check for required environment variables
        const requiredVars = ['VITE_API_URL', 'VITE_WS_URL'];
        requiredVars.forEach(varName => {
            if (content.includes(varName)) {
                success.push(`✅ ${varName} configured in ${envFile}`);
            } else {
                warnings.push(`⚠️  ${varName} not found in ${envFile}`);
            }
        });
        
        // Check for localhost URLs in production env
        if (envFile.includes('.production') && content.includes('localhost')) {
            warnings.push('⚠️  Production environment file contains localhost URLs');
        }
        
    } else {
        if (envFile.includes('.production')) {
            warnings.push(`⚠️  ${envFile} not found (optional but recommended)`);
        } else {
            warnings.push(`⚠️  ${envFile} not found`);
        }
    }
});

// Check if Vercel CLI is installed
const { execSync } = require('child_process');
try {
    execSync('vercel --version', { stdio: 'ignore' });
    success.push('✅ Vercel CLI installed');
} catch {
    warnings.push('⚠️  Vercel CLI not installed (install with: npm install -g vercel)');
}

// Output results
console.log('📊 Validation Results:');
console.log('======================\n');

if (success.length > 0) {
    console.log('🎉 Success:');
    success.forEach(msg => console.log(`  ${msg}`));
    console.log();
}

if (warnings.length > 0) {
    console.log('⚠️  Warnings:');
    warnings.forEach(msg => console.log(`  ${msg}`));
    console.log();
}

if (errors.length > 0) {
    console.log('❌ Errors:');
    errors.forEach(msg => console.log(`  ${msg}`));
    console.log();
}

// Summary
const total = success.length + warnings.length + errors.length;
console.log(`📈 Summary: ${success.length} success, ${warnings.length} warnings, ${errors.length} errors (${total} checks total)\n`);

if (errors.length === 0) {
    console.log('✅ Configuration is valid! Ready for Vercel deployment.\n');
    console.log('Next steps:');
    console.log('1. Run: vercel login');
    console.log('2. Run: vercel --prod');
    console.log('3. Configure environment variables in Vercel dashboard');
} else {
    console.log('❌ Please fix the errors above before deploying to Vercel.\n');
    process.exit(1);
}

console.log('\n🔗 Useful links:');
console.log('- Vercel Dashboard: https://vercel.com/dashboard');
console.log('- Vercel CLI Documentation: https://vercel.com/docs/cli');
console.log('- Deployment Guide: ./VERCEL_DEPLOYMENT.md');