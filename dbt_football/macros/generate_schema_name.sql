{#
    Use the schema set on each model (STAGING/INTERMEDIATE/MARTS) exactly as
    given, instead of dbt's default "<target_schema>_<custom_schema>"
    suffixing. Falls back to the target's default schema when a model
    doesn't set one.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
