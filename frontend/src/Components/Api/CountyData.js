import axios from "axios";

// Fetch basic data
//
// axios('http://127.0.0.1:8000/api/county/')
// .then(res => {
//     const counties = res.data
//     console.log(counties)
//     this.setState({ counties })
//     console.log(this.state.counties)
// })
// .catch(console.log)

export let countyRes = [];

function fetchCounty() {
    countyRes = axios.get("http://127.0.0.1:8000/api/county");
}

fetchCounty();
