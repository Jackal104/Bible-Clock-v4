const BibleScraper = require('bible-scraper');

async function testAMP() {
    try {
        // AMP translation ID for YouVersion
        const scraper = new BibleScraper(1588); // AMP ID
        const reference = 'Luke 12:57';
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

testAMP();