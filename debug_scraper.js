const BibleScraper = require('bible-scraper');

async function testScraper() {
    try {
        console.log('Testing bible-scraper directly...');
        
        // Test with AMP translation ID
        const scraper = new BibleScraper(1588);
        const reference = 'John 3:16';
        
        console.log(`Fetching ${reference} from YouVersion ID 1588 (AMP)...`);
        const result = await scraper.verse(reference);
        
        console.log('Result:', result);
    } catch (error) {
        console.log('Error:', error.message);
        console.log('Stack:', error.stack);
    }
}

testScraper();