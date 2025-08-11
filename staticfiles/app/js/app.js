var itemsReply = (function() {
  // Helper: Extract URLs from a text string using regex.
  const extractUrlsFromText = (text) => {
    const regex = /(https?:\/\/[^\s]+)/g;
    const urls = text.match(regex);
    return urls || [];
  };

  // Collect all tweet text elements (adjust this selector as needed)
  const tweetTextElements = document.querySelectorAll('[data-testid="tweetText"]');
  const tweets = [];

  tweetTextElements.forEach(tweetTextEl => {
    // Identify the tweet container; many tweets are wrapped in an <article> element.
    let tweetContainer = tweetTextEl.closest('article');
    if (!tweetContainer) {
      tweetContainer = tweetTextEl.parentElement;
    }
    
    // Extract tweet text
    const tweetText = tweetTextEl.textContent.trim();
    
    // Extract user details from data-testid "User-Name" if available
    const userNameEl = tweetContainer.querySelector('[data-testid="User-Name"] span');
    const userName = userNameEl ? userNameEl.textContent.trim() : null;
    
    // Extract user handle from the anchor's href in the container.
    const userLinkEl = tweetContainer.querySelector('div.css-175oi2r.r-1wbh5a2.r-dnmrzs a[role="link"]');
    let userHandle = null;
    if (userLinkEl) {
      userHandle = userLinkEl.getAttribute('href').replace(/^\//, '');
    }
    
    // Check if the user is verified (by looking for an svg with aria-label "Verified account")
    const verifiedEl = tweetContainer.querySelector('svg[aria-label="Verified account"]');
    const verified = !!verifiedEl;
    
    // Extract timestamp and tweet permalink from the <time> element inside an anchor
    const timeAnchor = tweetContainer.querySelector('a time');
    let timestamp = null;
    let tweetLink = null;
    if (timeAnchor) {
      timestamp = { 
        datetime: timeAnchor.getAttribute('datetime'), 
        display: timeAnchor.textContent.trim() 
      };
      tweetLink = timeAnchor.parentElement.getAttribute('href');  // Tweet permalink
    }
    
    // Skip tweet if timestamp is null (considered an ad)
    if (!timestamp) return;

    // Helper to extract numeric counts from a button based on its selector.
    const getCount = (selector) => {
      const btn = tweetContainer.querySelector(selector);
      if (!btn) return 0;
      const span = btn.querySelector('span');
      return span ? parseInt(span.textContent.trim(), 10) || 0 : 0;
    };

    // Extract engagement counts using data-testid attributes for reply, retweet, and like buttons.
    const replies = getCount('button[data-testid="reply"]');
    const retweets = getCount('button[data-testid="retweet"]');
    const likes = getCount('button[data-testid="like"]');
    
    // Extract views from an anchor with an aria-label containing "views"
    let views = 0;
    const analyticsLink = tweetContainer.querySelector('a[aria-label*="views"]');
    if (analyticsLink) {
      const span = analyticsLink.querySelector('span');
      views = span ? parseInt(span.textContent.trim(), 10) || 0 : 0;
    }
    
    // Construct the full reply link using x.com domain
    const replyLink = tweetLink ? `https://x.com${tweetLink}` : null;
    
    // Extract links inside the tweet text.
    // For t.co shortened links, attempt to use "data-expanded-url" attribute if available.
    const linkElements = tweetTextEl.querySelectorAll('a');
    const links = [];
    linkElements.forEach(linkEl => {
      let url = linkEl.getAttribute('href');
      // Ensure it's a real link (not an internal X.com link)
      if (url && !url.startsWith('/')) {
        if (url.startsWith('https://t.co')) {
          // Try to get the expanded URL from the attribute; if not, extract from the tweet text.
          const expanded = linkEl.getAttribute('data-expanded-url');
          if (expanded && expanded.trim() !== '') {
            url = expanded;
          } else {
            // Use regex to find proper URL in tweet text.
            const extractedUrls = extractUrlsFromText(tweetText);
            const realUrl = extractedUrls.find(u => !u.includes('t.co'));
            if (realUrl) {
              url = realUrl;
            }
          }
        }
        if (url.trim() !== '') {
          links.push(url);
        }
      }
    });
    
    // --- New: Check for media card preview with external link ---
    // Some tweets include an external link preview (media card).
    // We check for an element with data-testid="card.wrapper" and extract its <a> element.
    const cardLinkEl = tweetContainer.querySelector('[data-testid="card.wrapper"] a');
    if (cardLinkEl) {
      let mediaLink = cardLinkEl.getAttribute('href');
      if (mediaLink && mediaLink.startsWith('https://t.co')) {
        const expanded = cardLinkEl.getAttribute('data-expanded-url') || mediaLink;
        mediaLink = expanded;
      }
      if (mediaLink && mediaLink.trim() !== '' && !links.includes(mediaLink)) {
        links.push(mediaLink);
      }
    }
    
    tweets.push({
      user: {
        name: userName,
        handle: userHandle,
        verified: verified
      },
      timestamp: timestamp,
      tweetText: tweetText,
      engagement: {
        replies: replies,
        retweets: retweets,
        likes: likes,
        views: views
      },
      replyLink: replyLink,
      links: links  // Combined links from tweet text and media card
    });
  });
  
  // Filter out tweets that don't have any external links.
  const filteredTweets = tweets.filter(tweet => tweet.links.length > 0);

  // Output the structured data as JSON in the console.
  console.log(JSON.stringify(filteredTweets, null, 2));
  return filteredTweets;
})();

// New script to handle the "Copy to Clipboard" button

var autoScrollReplyScraper = (function() {
  let allTweets = [];
  let processedTweetIds = new Set();
  let scrollAttempts = 0;
  let maxScrollAttempts = 50; // Prevent infinite scrolling
  let scrollDelay = 2000; // 2 seconds between scrolls
  let noNewContentCounter = 0;
  let maxNoNewContent = 3; // Stop after 3 consecutive scrolls with no new content

  // Helper: Extract URLs from a text string using regex.
  const extractUrlsFromText = (text) => {
    const regex = /(https?:\/\/[^\s]+)/g;
    const urls = text.match(regex);
    return urls || [];
  };

  // Generate a unique ID for each tweet to avoid duplicates
  const generateTweetId = (tweet) => {
    return `${tweet.user.handle}-${tweet.timestamp?.datetime}-${tweet.tweetText.substring(0, 50)}`;
  };

  // Core scraping function
  const scrapeTweets = () => {
    console.log('🔍 Scraping current view...');
    
    // Collect all tweet text elements (adjust this selector as needed)
    const tweetTextElements = document.querySelectorAll('[data-testid="tweetText"]');
    const newTweets = [];
    let newTweetCount = 0;

    tweetTextElements.forEach(tweetTextEl => {
      // Identify the tweet container; many tweets are wrapped in an <article> element.
      let tweetContainer = tweetTextEl.closest('article');
      if (!tweetContainer) {
        tweetContainer = tweetTextEl.parentElement;
      }
      
      // Extract tweet text
      const tweetText = tweetTextEl.textContent.trim();
      
      // Extract user details from data-testid "User-Name" if available
      const userNameEl = tweetContainer.querySelector('[data-testid="User-Name"] span');
      const userName = userNameEl ? userNameEl.textContent.trim() : null;
      
      // Extract user handle from the anchor's href in the container.
      const userLinkEl = tweetContainer.querySelector('div.css-175oi2r.r-1wbh5a2.r-dnmrzs a[role="link"]');
      let userHandle = null;
      if (userLinkEl) {
        userHandle = userLinkEl.getAttribute('href').replace(/^\//, '');
      }
      
      // Check if the user is verified (by looking for an svg with aria-label "Verified account")
      const verifiedEl = tweetContainer.querySelector('svg[aria-label="Verified account"]');
      const verified = !!verifiedEl;
      
      // Extract timestamp and tweet permalink from the <time> element inside an anchor
      const timeAnchor = tweetContainer.querySelector('a time');
      let timestamp = null;
      let tweetLink = null;
      if (timeAnchor) {
        timestamp = { 
          datetime: timeAnchor.getAttribute('datetime'), 
          display: timeAnchor.textContent.trim() 
        };
        tweetLink = timeAnchor.parentElement.getAttribute('href');  // Tweet permalink
      }
      
      // Skip tweet if timestamp is null (considered an ad)
      if (!timestamp) return;

      // Helper to extract numeric counts from a button based on its selector.
      const getCount = (selector) => {
        const btn = tweetContainer.querySelector(selector);
        if (!btn) return 0;
        const span = btn.querySelector('span');
        return span ? parseInt(span.textContent.trim(), 10) || 0 : 0;
      };

      // Extract engagement counts using data-testid attributes for reply, retweet, and like buttons.
      const replies = getCount('button[data-testid="reply"]');
      const retweets = getCount('button[data-testid="retweet"]');
      const likes = getCount('button[data-testid="like"]');
      
      // Extract views from an anchor with an aria-label containing "views"
      let views = 0;
      const analyticsLink = tweetContainer.querySelector('a[aria-label*="views"]');
      if (analyticsLink) {
        const span = analyticsLink.querySelector('span');
        views = span ? parseInt(span.textContent.trim(), 10) || 0 : 0;
      }
      
      // Construct the full reply link using x.com domain
      const replyLink = tweetLink ? `https://x.com${tweetLink}` : null;
      
      // Extract links inside the tweet text.
      // For t.co shortened links, attempt to use "data-expanded-url" attribute if available.
      const linkElements = tweetTextEl.querySelectorAll('a');
      const links = [];
      linkElements.forEach(linkEl => {
        let url = linkEl.getAttribute('href');
        // Ensure it's a real link (not an internal X.com link)
        if (url && !url.startsWith('/')) {
          if (url.startsWith('https://t.co')) {
            // Try to get the expanded URL from the attribute; if not, extract from the tweet text.
            const expanded = linkEl.getAttribute('data-expanded-url');
            if (expanded && expanded.trim() !== '') {
              url = expanded;
            } else {
              // Use regex to find proper URL in tweet text.
              const extractedUrls = extractUrlsFromText(tweetText);
              const realUrl = extractedUrls.find(u => !u.includes('t.co'));
              if (realUrl) {
                url = realUrl;
              }
            }
          }
          if (url.trim() !== '') {
            links.push(url);
          }
        }
      });
      
      // --- Check for media card preview with external link ---
      // Some tweets include an external link preview (media card).
      // We check for an element with data-testid="card.wrapper" and extract its <a> element.
      const cardLinkEl = tweetContainer.querySelector('[data-testid="card.wrapper"] a');
      if (cardLinkEl) {
        let mediaLink = cardLinkEl.getAttribute('href');
        if (mediaLink && mediaLink.startsWith('https://t.co')) {
          const expanded = cardLinkEl.getAttribute('data-expanded-url') || mediaLink;
          mediaLink = expanded;
        }
        if (mediaLink && mediaLink.trim() !== '' && !links.includes(mediaLink)) {
          links.push(mediaLink);
        }
      }
      
      const tweet = {
        user: {
          name: userName,
          handle: userHandle,
          verified: verified
        },
        timestamp: timestamp,
        tweetText: tweetText,
        engagement: {
          replies: replies,
          retweets: retweets,
          likes: likes,
          views: views
        },
        replyLink: replyLink,
        links: links  // Combined links from tweet text and media card
      };

      // Only process tweets with external links and that we haven't seen before
      if (links.length > 0) {
        const tweetId = generateTweetId(tweet);
        if (!processedTweetIds.has(tweetId)) {
          processedTweetIds.add(tweetId);
          newTweets.push(tweet);
          newTweetCount++;
        }
      }
    });
    
    // Add new tweets to our collection
    allTweets.push(...newTweets);
    
    console.log(`✅ Found ${newTweetCount} new tweets with links (Total: ${allTweets.length})`);
    
    return newTweetCount;
  };

  // Function to scroll down the page
  const scrollDown = () => {
    const currentScrollY = window.scrollY;
    window.scrollTo(0, document.body.scrollHeight);
    
    // Alternative scroll methods if the above doesn't work
    if (window.scrollY === currentScrollY) {
      // Try scrolling by a large amount
      window.scrollBy(0, window.innerHeight * 2);
    }
    
    return window.scrollY !== currentScrollY;
  };

  // Check if we've reached the end of the page
  const isAtBottom = () => {
    return (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 100;
  };

  // Main auto-scroll function
  const autoScroll = async () => {
    console.log('🚀 Starting auto-scroll reply scraper...');
    console.log(`Settings: Max scrolls: ${maxScrollAttempts}, Delay: ${scrollDelay}ms`);
    
    return new Promise((resolve) => {
      const scrollAndScrape = () => {
        // Scrape current view
        const newTweetCount = scrapeTweets();
        
        // Track consecutive scrolls with no new content
        if (newTweetCount === 0) {
          noNewContentCounter++;
        } else {
          noNewContentCounter = 0;
        }
        
        // Check stopping conditions
        if (scrollAttempts >= maxScrollAttempts) {
          console.log(`⏹️ Stopped: Reached maximum scroll attempts (${maxScrollAttempts})`);
          resolve(allTweets);
          return;
        }
        
        if (noNewContentCounter >= maxNoNewContent) {
          console.log(`⏹️ Stopped: No new content found in ${maxNoNewContent} consecutive scrolls`);
          resolve(allTweets);
          return;
        }
        
        if (isAtBottom()) {
          console.log('⏹️ Stopped: Reached bottom of page');
          resolve(allTweets);
          return;
        }
        
        // Scroll down
        scrollAttempts++;
        console.log(`📜 Scrolling... (${scrollAttempts}/${maxScrollAttempts})`);
        
        const scrolled = scrollDown();
        if (!scrolled) {
          console.log('⏹️ Stopped: Could not scroll further');
          resolve(allTweets);
          return;
        }
        
        // Wait for content to load, then continue
        setTimeout(scrollAndScrape, scrollDelay);
      };
      
      // Start the process
      scrollAndScrape();
    });
  };

  // Configuration function
  const configure = (options = {}) => {
    if (options.maxScrollAttempts) maxScrollAttempts = options.maxScrollAttempts;
    if (options.scrollDelay) scrollDelay = options.scrollDelay;
    if (options.maxNoNewContent) maxNoNewContent = options.maxNoNewContent;
    
    console.log('⚙️ Configuration updated:', {
      maxScrollAttempts,
      scrollDelay,
      maxNoNewContent
    });
  };

  // Stop function
  const stop = () => {
    maxScrollAttempts = 0;
    console.log('🛑 Scraping stopped by user');
  };

  // Export results function
  const exportResults = () => {
    console.log('📊 Final Results:');
    console.log(`Total tweets with links found: ${allTweets.length}`);
    console.log('Full data:');
    console.log(JSON.stringify(allTweets, null, 2));
    
    // Also copy to clipboard if possible
    if (navigator.clipboard) {
      navigator.clipboard.writeText(JSON.stringify(allTweets, null, 2))
        .then(() => console.log('📋 Results copied to clipboard!'))
        .catch(() => console.log('❌ Could not copy to clipboard'));
    }
    
    return allTweets;
  };

  // Reset function to start fresh
  const reset = () => {
    allTweets = [];
    processedTweetIds.clear();
    scrollAttempts = 0;
    noNewContentCounter = 0;
    console.log('🔄 Scraper reset');
  };

  // Public API
  return {
    start: autoScroll,
    configure: configure,
    stop: stop,
    export: exportResults,
    reset: reset,
    getTweets: () => allTweets,
    getStats: () => ({
      totalTweets: allTweets.length,
      scrollAttempts: scrollAttempts,
      processedIds: processedTweetIds.size
    })
  };
})();

// Usage instructions
console.log(`
🎯 Auto-Scrolling X.com Reply Scraper Ready!

Basic Usage:
- autoScrollReplyScraper.start()  // Start scraping and scrolling

Configuration:
- autoScrollReplyScraper.configure({
    maxScrollAttempts: 100,    // Max number of scrolls (default: 50)
    scrollDelay: 3000,         // Delay between scrolls in ms (default: 2000)
    maxNoNewContent: 5         // Stop after X scrolls with no new content (default: 3)
  })

Controls:
- autoScrollReplyScraper.stop()     // Stop the scraping process
- autoScrollReplyScraper.export()   // View and copy results
- autoScrollReplyScraper.reset()    // Clear data and start fresh
- autoScrollReplyScraper.getStats() // Get current statistics

Example:
autoScrollReplyScraper.configure({ maxScrollAttempts: 100, scrollDelay: 1500 });
autoScrollReplyScraper.start().then(() => autoScrollReplyScraper.export());
`);






