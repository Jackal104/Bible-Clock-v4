const BibleScraper = require('bible-scraper');

async function testKJV() {
    try {
        // KJV translation ID for YouVersion
        const scraper = new BibleScraper(1); // KJV ID
        const reference = 'John 3:16';
        const result = await scraper.verse(reference);
        
        console.log(JSON.stringify({
            success: true,
            data: result,
            reference: reference
        }, null, 2));
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }, null, 2));
    }
}

testKJV();