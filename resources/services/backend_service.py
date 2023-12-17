from aws_cdk import aws_apigateway as apigateway
from constructs import Construct

from resources.dyndb import shortened_urls
from resources.roles import dyndb_crud, dyndb_list


class BackendService(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str
    ):
        super().__init__(scope, id)

        # create dynamodb table
        db_shortened_urls = shortened_urls.create(self)

        # create role for dynamodb crud
        dyndb_crud_role = dyndb_crud.create(
            self,
            table_arn=db_shortened_urls.table_arn
        )

        dyndb_list_role = dyndb_list.create(
            self,
            table_arn=db_shortened_urls.table_arn
        )

        # create the api gateway
        restapi = apigateway.RestApi(
            self,
            id="backend-api",
            rest_api_name="Backend API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS,
            ),
            # enable logging, data tracing, metrics, and x-ray tracing
            deploy_options=apigateway.StageOptions(
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                tracing_enabled=True,
            ),
            cloud_watch_role=True
        )

        # add shortened urls resource
        res_short_id = restapi.root.add_resource(
            "{shortId}",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS,
            )
        )

        res_short_id.add_method(
            "GET",
            integration=apigateway.AwsIntegration(
                service="dynamodb",
                action="GetItem",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    credentials_role=dyndb_crud_role,
                    request_templates={
                        "application/json": f"""
                        {{
                          "Key": {{
                            "id": {{
                              "S": "$input.params().path.shortId"
                            }}
                          }},
                          "TableName": "{db_shortened_urls.table_name}"
                        }}
                        """.strip()
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="301",
                            response_templates={
                                "application/json": """
                                #set($inputRoot = $input.path('$'))
                                #if ($inputRoot.toString().contains("Item"))
                                  #set($context.responseOverride.header.Location = $inputRoot.Item.url.S)
                                #end
                                """.strip()
                            },
                            response_parameters={
                                "method.response.header.Cache-Control": "'max-age=300'"
                            }
                        )
                    ]
                ),
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="301",
                    response_parameters={
                        "method.response.header.Location": True,
                        "method.response.header.Cache-Control": True
                    }
                )
            ]
        )

        # add delete shortened url resource DELETE, filter by owner == api key
        res_short_id.add_method(
            "DELETE",
            api_key_required=True,
            integration=apigateway.AwsIntegration(
                service="dynamodb",
                action="DeleteItem",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    credentials_role=dyndb_crud_role,
                    request_templates={
                        "application/json": f"""
                        {{
                          "TableName": "{db_shortened_urls.table_name}",
                          "Key": {{
                            "id": {{
                              "S": "$input.params().path.shortId"
                            }}
                          }},
                          "ConditionExpression": "#o = :o",
                          "ExpressionAttributeNames": {{
                            "#o": "owner"
                          }},
                          "ExpressionAttributeValues": {{
                            ":o": {{
                              "S": "$context.identity.apiKeyId"
                            }}
                          }}
                        }}
                        """.strip()
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200"
                        ), apigateway.IntegrationResponse(
                            status_code="400",
                            response_templates={
                                "application/json": """
                                #set($inputRoot = $input.path('$'))
                                #if($inputRoot.toString().contains("ConditionalCheckFailedException"))
                                  #set($context.responseOverride.status = 200)
                                  {"error": true,"message": "URL link does not exist"}
                                #end
                                """.strip()
                            }
                        )
                    ]
                ),
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200"
                ),
                apigateway.MethodResponse(
                    status_code="400"
                )
            ]
        )

        # add list shortened urls resource GET /shortened-urls
        res_shortened_urls = restapi.root.add_resource(
            "shortened-urls",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=apigateway.Cors.DEFAULT_HEADERS,
            )
        )

        res_shortened_urls.add_method(
            "GET",
            api_key_required=True,
            integration=apigateway.AwsIntegration(
                service="dynamodb",
                action="Query",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    credentials_role=dyndb_list_role,
                    request_templates={
                        "application/json": f"""
                                {{
                                  "TableName": "{db_shortened_urls.table_name}",
                                  "IndexName": "owner-index",
                                  "KeyConditionExpression": "#o = :o",
                                  "ExpressionAttributeNames": {{
                                    "#o": "owner"
                                  }},
                                  "ExpressionAttributeValues": {{
                                    ":o": {{
                                      "S": "$context.identity.apiKeyId"
                                    }}
                                  }}
                                }}
                                """.strip()
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_templates={
                                "application/json": """
                                        #set($inputRoot = $input.path('$'))
                                        [
                                          #foreach($elem in $inputRoot.Items) {
                                            "id": "$elem.id.S",
                                            "url": "$elem.url.S",
                                            "timestamp": "$elem.timestamp.S",
                                            "owner": "$elem.owner.S"
                                          }#if ($foreach.hasNext),#end
                                          #end
                                        ]
                                        """.strip()
                            }
                        )
                    ]
                ),
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200"
                )
            ]
        )

        # add create shortened url resource POST
        res_shortened_urls.add_method(
            "POST",
            api_key_required=True,
            integration=apigateway.AwsIntegration(
                service="dynamodb",
                action="UpdateItem",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                    credentials_role=dyndb_crud_role,
                    request_templates={
                        "application/json": f"""
                                {{
                                  "TableName": "{db_shortened_urls.table_name}",
                                  "ConditionExpression": "attribute_not_exists(id)",
                                  "Key": {{
                                    "id": {{
                                      "S": $input.json('$.shortId')
                                    }}
                                  }},
                                  "ExpressionAttributeNames": {{
                                    "#u": "url",
                                    "#o": "owner",
                                    "#ts": "timestamp"
                                  }},
                                  "ExpressionAttributeValues": {{
                                    ":u": {{
                                      "S": $input.json('$.url')
                                    }},
                                    ":o": {{
                                      "S": "$context.identity.apiKeyId"
                                    }},
                                    ":ts": {{
                                      "S": "$context.requestTime"
                                    }}
                                  }},
                                  "UpdateExpression": "SET #u = :u, #o = :o, #ts = :ts",
                                  "ReturnValues": "ALL_NEW"
                                }}
                                """.strip()
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            response_templates={
                                "application/json": """
                                        #set($inputRoot = $input.path('$'))
                                        {
                                          "id": "$inputRoot.Attributes.id.S",
                                          "url": "$inputRoot.Attributes.url.S",
                                          "timestamp": "$inputRoot.Attributes.timestamp.S",
                                          "owner": "$inputRoot.Attributes.owner.S"
                                        }
                                        """.strip()
                            }
                        ), apigateway.IntegrationResponse(
                            status_code="400",
                            response_templates={
                                "application/json": """
                                        #set($inputRoot = $input.path('$'))
                                        #if($inputRoot.toString().contains("ConditionalCheckFailedException"))
                                          #set($context.responseOverride.status = 200)
                                          {"error": true,"message": "URL link already exists"}
                                        #end
                                        """.strip()
                            }
                        )
                    ]
                ),
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200"
                ),
                apigateway.MethodResponse(
                    status_code="400"
                )
            ]
        )

        # add usage plan to api gateway
        usage_plan = restapi.add_usage_plan(
            id="usage_plan",
            name="backend_usage_plan",
            throttle=apigateway.ThrottleSettings(
                rate_limit=10,
                burst_limit=2
            )
        )
        usage_plan.add_api_stage(
            stage=restapi.deployment_stage
        )
