###  endpoint for correlation endpoint

- The endpoint for correlation is 
```python

 /api/correlation/compute/corr_compute
```


**To  be noted before  spinning the server for correlation computation\which can be set for example env 
SQL_URI=mysql://user:password@localhost/db_webqtl and also to GENENETWORK_FILES default is HOME+"/data/genotype_files**

(required  input data *should be in json format*)
- "primary_samples": "",
- "trait_id"
- "dataset"
- "sample_vals"
- "corr_type"
- "corr_dataset"
- "corr_return_results"
- "corr_samples_group"
- "corr_sample_method"
- "min_expr"
- "location_type"
- "loc_chr"
- "min_loc_mb"
- "max_loc_mb"
- "p_range_lower"
- "p_range_upper"

- example

```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"primary_samles":"",trait_id:"","dataset":"","sample_vals":"","corr_type":"",corr_sample_group:"",corr_sample_method:""}' \
    localhost:5000/api/correlation/correlation_compute

 ```


- output data is correlation_json 

