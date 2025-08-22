"""
Multi-operation viewset for executing multiple operations atomically.
Provides create, update, and delete operations across different models in a single transaction.
"""

import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..serializers.batch_operations import MultiOperationSerializer
from .mixins import WorkspaceValidationMixin


class MultiOperationsViewSet(WorkspaceValidationMixin, viewsets.ViewSet):
    """
    ViewSet for executing multiple operations atomically.
    
    Provides a single endpoint for executing multiple create, update, and delete
    operations across different models in a single database transaction.
    
    URL: /api/v1/workspaces/{workspace_id}/multi-operations/
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Multi Operations"],
        methods=['post'],
        request=MultiOperationSerializer,
        summary="Execute multiple operations atomically",
        description="""
        Execute multiple create, update, and delete operations in a single transaction.
        
        **Supported operation types:**
        
        **String Operations:**
        - `create_string`: Create new string with details
        - `update_string`: Update existing string
        - `delete_string`: Delete string and related details
        - `update_string_parent`: Update string parent relationship
        
        **String Detail Operations:**
        - `create_string_detail`: Create new string detail
        - `update_string_detail`: Update existing string detail
        - `delete_string_detail`: Delete string detail
        
        **Submission Operations:**
        - `create_submission`: Create new submission
        - `update_submission`: Update existing submission
        - `delete_submission`: Delete submission and related strings
        
        **Transaction Guarantees:**
        - All operations must succeed for the transaction to commit
        - If any operation fails, all changes are rolled back
        - Operations are executed in the order provided
        - Each operation is validated before execution
        
        **Example Request (Single Items):**
        ```json
        {
          "operations": [
            {
              "type": "update_string_detail",
              "data": {"id": 154, "dimension_value": 3}
            },
            {
              "type": "update_string_parent",
              "data": {"string_id": 88, "parent_id": 45}
            }
          ]
        }
        ```
        
        **Example Request (Grouped Array):**
        ```json
        {
          "operations": [
            {
              "type": "update_string_detail",
              "data": [
                {"id": 154, "dimension_value": 3},
                {"id": 157, "dimension_value_freetext": "2"}
              ]
            },
            {
              "type": "update_string_parent",
              "data": {"string_id": 88, "parent_id": 45}
            }
          ]
        }
        ```
        """,
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: {
                'description': 'All operations completed successfully',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'transaction_id': {
                                    'type': 'string', 
                                    'format': 'uuid',
                                    'description': 'Unique identifier for this transaction'
                                },
                                'status': {
                                    'type': 'string',
                                    'enum': ['completed'],
                                    'description': 'Transaction status'
                                },
                                'total_operations': {
                                    'type': 'integer',
                                    'description': 'Total number of operation groups requested'
                                },
                                'total_individual_operations': {
                                    'type': 'integer',
                                    'description': 'Total number of individual operations executed'
                                },
                                'successful_operations': {
                                    'type': 'integer',
                                    'description': 'Number of operation groups that completed successfully'
                                },
                                'results': {
                                    'type': 'array',
                                    'description': 'Results for each operation',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'operation_index': {
                                                'type': 'integer',
                                                'description': 'Index of the operation in the request array'
                                            },
                                            'type': {
                                                'type': 'string',
                                                'description': 'Type of operation that was executed'
                                            },
                                            'status': {
                                                'type': 'string',
                                                'enum': ['success'],
                                                'description': 'Operation status'
                                            },
                                            'count': {
                                                'type': 'integer',
                                                'description': 'Number of items processed in this operation'
                                            },
                                            'results': {
                                                'oneOf': [
                                                    {
                                                        'type': 'object',
                                                        'description': 'Single result (when count=1)'
                                                    },
                                                    {
                                                        'type': 'array',
                                                        'description': 'Array of results (when count>1)',
                                                        'items': {'type': 'object'}
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            400: {
                'description': 'Validation error or operation failure',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {
                                    'type': 'string',
                                    'description': 'Error message describing what went wrong'
                                },
                                'transaction_id': {
                                    'type': 'string',
                                    'format': 'uuid',
                                    'description': 'Transaction ID (for failed transactions)'
                                },
                                'status': {
                                    'type': 'string',
                                    'enum': ['failed'],
                                    'description': 'Transaction status'
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def execute(self, request, *args, **kwargs):
        """Execute multiple operations atomically."""
        try:
            serializer = MultiOperationSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            # Execute all operations
            workspace_id = getattr(request, 'workspace_id', None)
            user = getattr(request, 'user', None)
            
            result = serializer.execute(workspace_id, user)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            # This will cause the entire transaction to rollback
            return Response({
                'error': f'Multi-operation transaction failed: {str(e)}',
                'transaction_id': str(uuid.uuid4()),
                'status': 'failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=["Multi Operations"],
        methods=['post'],
        request=MultiOperationSerializer,
        summary="Validate operations without executing",
        description="""
        Validate a batch of operations without executing them.
        
        This endpoint is useful for:
        - Checking operation validity before execution
        - Testing operation configurations
        - Validating complex multi-step workflows
        
        **Response includes:**
        - Validation status (valid/invalid)
        - Total number of operations
        - Detailed validation results
        - Error messages for invalid operations
        
        **Example Request:**
        ```json
        {
          "operations": [
            {
              "type": "update_string_detail",
              "data": {"id": 154, "dimension_value": 3}
            }
          ]
        }
        ```
        """,
        parameters=[
            OpenApiParameter(
                name='workspace_id',
                description='Workspace ID',
                required=True,
                type=int,
                location=OpenApiParameter.PATH
            )
        ],
        responses={
            200: {
                'description': 'Operations validation completed',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'status': {
                                    'type': 'string',
                                    'enum': ['valid', 'invalid'],
                                    'description': 'Validation status'
                                },
                                'total_operations': {
                                    'type': 'integer',
                                    'description': 'Total number of operations validated'
                                },
                                'message': {
                                    'type': 'string',
                                    'description': 'Validation result message'
                                },
                                'error': {
                                    'type': 'string',
                                    'description': 'Error message if validation failed'
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate_operations(self, request, *args, **kwargs):
        """Validate operations without executing them."""
        try:
            serializer = MultiOperationSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'status': 'valid',
                'total_operations': len(serializer.validated_data['operations']),
                'message': 'All operations are valid and ready for execution'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'invalid',
                'error': str(e),
                'total_operations': 0
            }, status=status.HTTP_200_OK)  # Use 200 for validation results
