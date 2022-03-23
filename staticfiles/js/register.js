document.addEventListener("DOMContentLoaded", function() {
    const existing_company = document.getElementById("existing_company");
    const existing_company_div = document.getElementById("existing_company_div");
    const company_code = document.getElementById("company_code");

    const new_company = document.getElementById("new_company");
    const new_company_div = document.getElementById("new_company_div");
    const company_full_name = document.getElementById("company_full_name");
    const company_short_name = document.getElementById("company_short_name");

    existing_company.onclick = function() {
        existing_company_div.style.display = "block";
        company_code.required = true;

        new_company_div.style.display = "none";
        company_full_name.required = false;
        company_short_name.required = false;
    }

    new_company.onclick = function() {
        new_company_div.style.display = "block";
        company_full_name.required = true;
        company_short_name.required = true;

        existing_company_div.style.display = "none";
        company_code.required = false;
    }
})