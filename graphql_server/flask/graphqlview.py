import copy
from collections.abc import MutableMapping
from functools import partial
from typing import List

from flask import Response, render_template_string, request
from flask.views import View
from graphql import specified_rules
from graphql.error import GraphQLError
from graphql.type.schema import GraphQLSchema

from graphql_server import (
    GraphQLParams,
    HttpQueryError,
    _check_jinja,
    encode_execution_results,
    format_error_default,
    json_encode,
    load_json_body,
    run_http_query,
)
from graphql_server.render_graphiql import (
    GraphiQLConfig,
    GraphiQLData,
    GraphiQLOptions,
    render_graphiql_sync,
)


class GraphQLView(View):
    schema = None
    root_value = None
    context = None
    pretty = False
    graphiql = False
    graphiql_version = None
    graphiql_template = None
    graphiql_html_title = None
    middleware = None
    validation_rules = None
    execution_context_class = None
    batch = False
    jinja_env = None
    subscriptions = None
    headers = None
    default_query = None
    header_editor_enabled = None
    should_persist_headers = None

    methods = ["GET", "POST", "PUT", "DELETE"]

    format_error = staticmethod(format_error_default)
    encode = staticmethod(json_encode)

    def __init__(self, **kwargs):
        """Creates an instance of the GraphQLView class with the provided keyword arguments.
        Parameters:
            - kwargs (dict): Keyword arguments used to set attributes of the GraphQLView instance.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Set attributes using keyword arguments.
            - Check if provided schema is a GraphQLSchema instance.
            - If not, check if it is wrapped in a Graphene schema.
            - If not, raise a TypeError.
            - Check if a Jinja environment is provided.
            - If so, check if it is a valid Jinja environment."""

        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if not isinstance(self.schema, GraphQLSchema):
            # maybe the GraphQL schema is wrapped in a Graphene schema
            self.schema = getattr(self.schema, "graphql_schema", None)
            if not isinstance(self.schema, GraphQLSchema):
                raise TypeError("A Schema is required to be provided to GraphQLView.")

        if self.jinja_env is not None:
            _check_jinja(self.jinja_env)

    def get_root_value(self):
        """ "Returns the root value of the current object."
        Parameters:
            - self (object): The current object.
        Returns:
            - root_value (type): The root value of the current object.
        Processing Logic:
            - Get the root value from the current object.
            - No additional processing logic needed."""

        return self.root_value

    def get_context(self):
        """"""

        context = (
            copy.copy(self.context)
            if self.context is not None and isinstance(self.context, MutableMapping)
            else {}
        )
        if isinstance(context, MutableMapping) and "request" not in context:
            context.update({"request": request})
        return context

    def get_middleware(self):
        """"""

        return self.middleware

    def get_validation_rules(self):
        """"""

        if self.validation_rules is None:
            return specified_rules
        return self.validation_rules

    def get_execution_context_class(self):
        """"""

        return self.execution_context_class

    def dispatch_request(self):
        """"""

        try:
            request_method = request.method.lower()
            data = self.parse_body()

            show_graphiql = request_method == "get" and self.should_display_graphiql()
            catch = show_graphiql

            pretty = self.pretty or show_graphiql or request.args.get("pretty")

            all_params: List[GraphQLParams]
            execution_results, all_params = run_http_query(
                self.schema,
                request_method,
                data,
                query_data=request.args,
                batch_enabled=self.batch,
                catch=catch,
                # Execute options
                root_value=self.get_root_value(),
                context_value=self.get_context(),
                middleware=self.get_middleware(),
                validation_rules=self.get_validation_rules(),
                execution_context_class=self.get_execution_context_class(),
            )
            result, status_code = encode_execution_results(
                execution_results,
                is_batch=isinstance(data, list),
                format_error=self.format_error,
                encode=partial(self.encode, pretty=pretty),
            )

            if show_graphiql:
                graphiql_data = GraphiQLData(
                    result=result,
                    query=all_params[0].query,
                    variables=all_params[0].variables,
                    operation_name=all_params[0].operation_name,
                    subscription_url=self.subscriptions,
                    headers=self.headers,
                )
                graphiql_config = GraphiQLConfig(
                    graphiql_version=self.graphiql_version,
                    graphiql_template=self.graphiql_template,
                    graphiql_html_title=self.graphiql_html_title,
                    jinja_env=self.jinja_env,
                )
                graphiql_options = GraphiQLOptions(
                    default_query=self.default_query,
                    header_editor_enabled=self.header_editor_enabled,
                    should_persist_headers=self.should_persist_headers,
                )
                source = render_graphiql_sync(
                    data=graphiql_data, config=graphiql_config, options=graphiql_options
                )
                return render_template_string(source)

            return Response(result, status=status_code, content_type="application/json")

        except HttpQueryError as e:
            parsed_error = GraphQLError(e.message)
            return Response(
                self.encode({"errors": [self.format_error(parsed_error)]}),
                status=e.status_code,
                headers=e.headers,
                content_type="application/json",
            )

    @staticmethod
    def parse_body():
        """"""

        # We use mimetype here since we don't need the other
        # information provided by content_type
        if (content_type := request.mimetype) == "application/graphql":
            return {"query": request.data.decode("utf8")}

        elif content_type == "application/json":
            return load_json_body(request.data.decode("utf8"))

        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return request.form

        return {}

    def should_display_graphiql(self):
        """"""

        if not self.graphiql or "raw" in request.args:
            return False

        return self.request_wants_html()

    @staticmethod
    def request_wants_html():
        """"""

        best = request.accept_mimetypes.best_match(["application/json", "text/html"])
        return (
            best == "text/html"
            and request.accept_mimetypes[best]
            > request.accept_mimetypes["application/json"]
        )
