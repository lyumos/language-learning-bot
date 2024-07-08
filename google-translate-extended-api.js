const translate = require('google-translate-extended-api');

process.stdout.setEncoding('utf8');

const text = process.argv[2];
const fromLang = process.argv[3];
const toLang = process.argv[4];

translate(text, fromLang, toLang).then((res) => {
    console.log(JSON.stringify(res, null, 2));
}).catch((err) => {
    console.error(err);
});