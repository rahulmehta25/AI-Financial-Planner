#!/usr/bin/env node

// Script to create demo user in Supabase
// Run with: node scripts/create-demo-user.js

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// You need to use the service role key for admin operations
// Get this from your Supabase project settings > API
const SUPABASE_URL = process.env.VITE_SUPABASE_URL || 'https://tqxhvrsdroafvigbgaxx.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY; // You need to add this to .env

if (!SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Error: SUPABASE_SERVICE_ROLE_KEY is not set in environment variables');
  console.log('Please add it to your .env file');
  console.log('You can find it in your Supabase project settings > API > service_role key');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

async function createDemoUser() {
  console.log('Creating demo user...');
  
  try {
    // First check if user already exists
    const { data: existingUser } = await supabase.auth.admin.getUserByEmail('demo@financeai.com');
    
    if (existingUser && existingUser.user) {
      console.log('Demo user already exists with ID:', existingUser.user.id);
      await createDemoData(existingUser.user.id);
      return;
    }

    // Create new demo user
    const { data, error } = await supabase.auth.admin.createUser({
      email: 'demo@financeai.com',
      password: 'demo123',
      email_confirm: true,
      user_metadata: {
        full_name: 'Demo User'
      }
    });

    if (error) {
      console.error('Error creating demo user:', error);
      return;
    }

    console.log('Demo user created successfully!');
    console.log('User ID:', data.user.id);
    console.log('Email:', data.user.email);
    
    // Create demo data for the user
    await createDemoData(data.user.id);
    
  } catch (error) {
    console.error('Unexpected error:', error);
  }
}

async function createDemoData(userId) {
  console.log('\nCreating demo data for user:', userId);
  
  try {
    // Create demo portfolio
    const { data: portfolio, error: portfolioError } = await supabase
      .from('portfolios')
      .insert({
        user_id: userId,
        name: 'Demo Portfolio',
        description: 'A sample portfolio for demonstration purposes',
        is_default: true
      })
      .select()
      .single();

    if (portfolioError) {
      if (portfolioError.code === '23505') { // Unique constraint violation
        console.log('Demo portfolio already exists');
        const { data: existingPortfolio } = await supabase
          .from('portfolios')
          .select()
          .eq('user_id', userId)
          .eq('name', 'Demo Portfolio')
          .single();
        
        if (existingPortfolio) {
          console.log('Using existing portfolio:', existingPortfolio.id);
          return;
        }
      } else {
        console.error('Error creating portfolio:', portfolioError);
        return;
      }
    }

    if (!portfolio) {
      console.error('Portfolio was not created');
      return;
    }

    console.log('Portfolio created:', portfolio.id);

    // Create demo holdings
    const holdings = [
      { symbol: 'AAPL', quantity: 50, cost_basis: 150.00, purchase_date: '2024-01-15', asset_type: 'stock', current_price: 175.00 },
      { symbol: 'GOOGL', quantity: 20, cost_basis: 120.00, purchase_date: '2024-02-01', asset_type: 'stock', current_price: 145.00 },
      { symbol: 'MSFT', quantity: 30, cost_basis: 300.00, purchase_date: '2024-01-20', asset_type: 'stock', current_price: 380.00 },
      { symbol: 'TSLA', quantity: 15, cost_basis: 200.00, purchase_date: '2024-03-01', asset_type: 'stock', current_price: 250.00 },
      { symbol: 'BTC', quantity: 0.5, cost_basis: 40000.00, purchase_date: '2024-01-01', asset_type: 'crypto', current_price: 65000.00 },
      { symbol: 'ETH', quantity: 5, cost_basis: 2000.00, purchase_date: '2024-02-15', asset_type: 'crypto', current_price: 3500.00 }
    ];

    for (const holding of holdings) {
      const current_value = holding.quantity * holding.current_price;
      const total_cost = holding.quantity * holding.cost_basis;
      const gain_loss = current_value - total_cost;
      const gain_loss_percent = (gain_loss / total_cost) * 100;

      const { error: holdingError } = await supabase
        .from('holdings')
        .insert({
          portfolio_id: portfolio.id,
          ...holding,
          current_value,
          gain_loss,
          gain_loss_percent
        });

      if (holdingError) {
        console.error(`Error creating holding ${holding.symbol}:`, holdingError);
      } else {
        console.log(`Created holding: ${holding.symbol}`);
      }
    }

    // Create demo transactions
    const transactions = [
      { symbol: 'AAPL', transaction_type: 'buy', quantity: 50, price: 150.00, transaction_date: '2024-01-15', notes: 'Initial purchase' },
      { symbol: 'GOOGL', transaction_type: 'buy', quantity: 20, price: 120.00, transaction_date: '2024-02-01', notes: 'Adding to position' },
      { symbol: 'MSFT', transaction_type: 'buy', quantity: 30, price: 300.00, transaction_date: '2024-01-20', notes: 'Long term hold' },
      { symbol: 'TSLA', transaction_type: 'buy', quantity: 15, price: 200.00, transaction_date: '2024-03-01', notes: 'Speculative buy' },
      { symbol: 'BTC', transaction_type: 'buy', quantity: 0.5, price: 40000.00, transaction_date: '2024-01-01', notes: 'Crypto allocation' },
      { symbol: 'ETH', transaction_type: 'buy', quantity: 5, price: 2000.00, transaction_date: '2024-02-15', notes: 'Diversifying crypto' }
    ];

    for (const transaction of transactions) {
      const total_amount = transaction.quantity * transaction.price;
      
      const { error: transactionError } = await supabase
        .from('transactions')
        .insert({
          portfolio_id: portfolio.id,
          ...transaction,
          total_amount
        });

      if (transactionError) {
        console.error(`Error creating transaction for ${transaction.symbol}:`, transactionError);
      } else {
        console.log(`Created transaction: ${transaction.transaction_type} ${transaction.symbol}`);
      }
    }

    // Create demo goals
    const goals = [
      { name: 'Emergency Fund', target_amount: 10000.00, current_amount: 7500.00, target_date: '2025-06-01', category: 'Safety', priority: 1 },
      { name: 'Vacation Fund', target_amount: 5000.00, current_amount: 2000.00, target_date: '2025-12-01', category: 'Lifestyle', priority: 3 },
      { name: 'Home Down Payment', target_amount: 50000.00, current_amount: 15000.00, target_date: '2026-12-31', category: 'Real Estate', priority: 2 },
      { name: 'Retirement', target_amount: 1000000.00, current_amount: 76800.00, target_date: '2055-01-01', category: 'Retirement', priority: 1 }
    ];

    for (const goal of goals) {
      const { error: goalError } = await supabase
        .from('goals')
        .insert({
          user_id: userId,
          ...goal
        });

      if (goalError) {
        console.error(`Error creating goal ${goal.name}:`, goalError);
      } else {
        console.log(`Created goal: ${goal.name}`);
      }
    }

    console.log('\n✅ Demo data created successfully!');
    console.log('\nYou can now login with:');
    console.log('Email: demo@financeai.com');
    console.log('Password: demo123');
    
  } catch (error) {
    console.error('Error creating demo data:', error);
  }
}

// Run the script
createDemoUser().then(() => {
  console.log('\nScript completed');
  process.exit(0);
}).catch(error => {
  console.error('Script failed:', error);
  process.exit(1);
});