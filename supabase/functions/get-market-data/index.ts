// Edge Function for fetching market data from Yahoo Finance
import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface MarketDataRequest {
  action: 'quote' | 'historical' | 'batch' | 'search'
  symbols?: string | string[]
  period?: string // 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, ytd
  interval?: string // 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
}

Deno.serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { action, symbols, period = '1y', interval = '1d' } = await req.json() as MarketDataRequest

    let data: any

    switch (action) {
      case 'quote':
        data = await fetchQuotes(symbols as string | string[])
        break
      
      case 'historical':
        data = await fetchHistorical(symbols as string, period, interval)
        break
      
      case 'batch':
        data = await fetchBatchQuotes(symbols as string[])
        break
      
      case 'search':
        data = await searchSymbols(symbols as string)
        break
      
      default:
        throw new Error(`Unknown action: ${action}`)
    }

    // Optional: Cache in Supabase database
    if (action === 'quote' && data) {
      await cacheMarketData(symbols as string, data)
    }

    return new Response(
      JSON.stringify(data),
      { 
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=60' // Cache for 1 minute
        } 
      }
    )
  } catch (error) {
    console.error('Market data error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 400,
        headers: { 
          ...corsHeaders,
          'Content-Type': 'application/json' 
        } 
      }
    )
  }
})

async function fetchQuotes(symbols: string | string[]): Promise<any> {
  const symbolList = Array.isArray(symbols) ? symbols.join(',') : symbols
  
  try {
    // Yahoo Finance API v7 (free, no key required)
    const response = await fetch(
      `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${symbolList}`
    )
    
    if (!response.ok) {
      throw new Error(`Yahoo Finance API error: ${response.status}`)
    }
    
    const data = await response.json()
    const quotes = data.quoteResponse.result
    
    // Transform to our format
    return quotes.map((quote: any) => ({
      symbol: quote.symbol,
      name: quote.longName || quote.shortName,
      price: quote.regularMarketPrice,
      change: quote.regularMarketChange,
      changePercent: quote.regularMarketChangePercent,
      previousClose: quote.regularMarketPreviousClose,
      open: quote.regularMarketOpen,
      dayHigh: quote.regularMarketDayHigh,
      dayLow: quote.regularMarketDayLow,
      volume: quote.regularMarketVolume,
      marketCap: quote.marketCap,
      fiftyTwoWeekHigh: quote.fiftyTwoWeekHigh,
      fiftyTwoWeekLow: quote.fiftyTwoWeekLow,
      dividendYield: quote.dividendYield,
      pe: quote.trailingPE,
      eps: quote.epsTrailingTwelveMonths,
      timestamp: new Date().toISOString()
    }))
  } catch (error) {
    console.error('Error fetching quotes:', error)
    // Fallback to cached data if available
    return getCachedData(symbolList)
  }
}

async function fetchHistorical(symbol: string, period: string, interval: string): Promise<any> {
  try {
    // Calculate timestamps
    const end = Math.floor(Date.now() / 1000)
    let start = end
    
    switch (period) {
      case '1d': start = end - 86400; break
      case '5d': start = end - 432000; break
      case '1mo': start = end - 2592000; break
      case '3mo': start = end - 7776000; break
      case '6mo': start = end - 15552000; break
      case '1y': start = end - 31536000; break
      case '2y': start = end - 63072000; break
      case '5y': start = end - 157680000; break
      case 'ytd': 
        const now = new Date()
        const yearStart = new Date(now.getFullYear(), 0, 1)
        start = Math.floor(yearStart.getTime() / 1000)
        break
    }
    
    // Yahoo Finance historical data
    const response = await fetch(
      `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?period1=${start}&period2=${end}&interval=${interval}`
    )
    
    if (!response.ok) {
      throw new Error(`Yahoo Finance API error: ${response.status}`)
    }
    
    const data = await response.json()
    const result = data.chart.result[0]
    const quotes = result.indicators.quote[0]
    const timestamps = result.timestamp
    
    // Transform to OHLCV format
    const historical = timestamps.map((timestamp: number, i: number) => ({
      date: new Date(timestamp * 1000).toISOString().split('T')[0],
      open: quotes.open[i],
      high: quotes.high[i],
      low: quotes.low[i],
      close: quotes.close[i],
      volume: quotes.volume[i]
    })).filter((item: any) => item.close !== null)
    
    return {
      symbol,
      period,
      interval,
      data: historical
    }
  } catch (error) {
    console.error('Error fetching historical data:', error)
    return { error: error.message }
  }
}

async function fetchBatchQuotes(symbols: string[]): Promise<any> {
  // Fetch multiple quotes in parallel
  const promises = symbols.map(symbol => fetchQuotes(symbol))
  const results = await Promise.allSettled(promises)
  
  return results.map((result, index) => ({
    symbol: symbols[index],
    data: result.status === 'fulfilled' ? result.value[0] : null,
    error: result.status === 'rejected' ? result.reason.message : null
  }))
}

async function searchSymbols(query: string): Promise<any> {
  try {
    const response = await fetch(
      `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&quotesCount=10`
    )
    
    if (!response.ok) {
      throw new Error(`Yahoo Finance API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    return data.quotes.map((quote: any) => ({
      symbol: quote.symbol,
      name: quote.longname || quote.shortname,
      type: quote.quoteType,
      exchange: quote.exchange,
      sector: quote.sector,
      industry: quote.industry
    }))
  } catch (error) {
    console.error('Error searching symbols:', error)
    return { error: error.message }
  }
}

async function cacheMarketData(symbol: string, data: any): Promise<void> {
  try {
    // Initialize Supabase client with service role key for caching
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)
    
    // Upsert into cache table
    await supabase
      .from('market_data_cache')
      .upsert({
        symbol,
        data,
        data_type: 'quote',
        updated_at: new Date().toISOString()
      })
      .select()
  } catch (error) {
    console.error('Cache error:', error)
    // Don't throw - caching is optional
  }
}

async function getCachedData(symbol: string): Promise<any> {
  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)
    
    const { data, error } = await supabase
      .from('market_data_cache')
      .select('data')
      .eq('symbol', symbol)
      .single()
    
    if (error) throw error
    return data?.data
  } catch (error) {
    console.error('Cache fetch error:', error)
    return null
  }
}

/* To invoke locally:

  1. Run `supabase start` (see: https://supabase.com/docs/reference/cli/supabase-start)
  2. Make an HTTP request:

  curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/get-market-data' \
    --header 'Authorization: Bearer YOUR_ANON_KEY' \
    --header 'Content-Type: application/json' \
    --data '{"action":"quote","symbols":"AAPL"}'

*/
