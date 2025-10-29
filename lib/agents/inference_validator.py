# inference validator

# %%
"""
inference_validator.py

Validate the inference of a model using the toulmin model of argumentation.
- If the inference is not valid, return the reason why.
- If the inference is valid, return the reason why.
- If the inference is not valid, return the reason why.
"""

# %%


from enum import Enum

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.llm_models import gpt_5_model
from lib.models.agent import DEFAULT_LLM_TIMEOUT, AgentProtocol


class WarrantExpression(str, Enum):
    STATED = "stated"
    IMPLIED = "implied"
    NONE = "none"


class ToulminClaim(BaseModel):
    text: str = Field(
        description="The exact excerpt from the chunk that implies the claim"
    )
    claim: str = Field(
        description="The claim or inferential conclusion made within the excerpt"
    )
    # rationale: str = Field(
    #     description="Why the excerpt implies this claim (brief analytic rationale)"
    # )

    # Toulmin elements
    data: list[str] = Field(
        default_factory=list,
        description=(
            "Data/Grounds: evidence or facts supporting the claim, quoted or paraphrased as taken from the preceding text."
        ),
    )
    warrants: list[str] = Field(
        default_factory=list,
        description=(
            "Warrants: assumptions that connect the data to the claim (may be cultural, logical, or methodological). Follows from the domain context or related references."
        ),
    )
    warrant_expression: WarrantExpression = Field(
        description=(
            "Whether the primary warrant is stated explicitly, implied implicitly, or none could be identified"
        )
    )
    qualifiers: list[str] = Field(
        default_factory=list,
        description=(
            "Qualifiers: words/phrases indicating the strength/scope of the claim (e.g., 'likely', 'some', 'in many cases'). Helps determine if the claim has been overstated or understated."
        ),
    )
    rebuttals: list[str] = Field(
        default_factory=list,
        description=(
            "Rebuttals: acknowledged exceptions, counter-arguments, or conditions under which the claim may not hold. Helps determine if the claim has been overstated or understated."
        ),
    )
    backing: list[str] = Field(
        default_factory=list,
        description=(
            "Backing: additional support that justifies the warrant (e.g., principles, studies, or theoretical reasons). Helps determine if the claim has been overstated or understated."
        ),
    )


class InferenceValidationResponse(BaseModel):
    valid: bool = Field(
        description="Considering the Toulmin elements, whether the inference is valid or not"
    )
    rationale: str = Field(
        description="The rationale for why you think the inference is valid or not. If the inference is not valid, explain why. If the inference is valid, explain why. In only TWO sentences."
    )
    suggested_action: str = Field(
        description="A suggested action to take if the inference is not valid. If the inference is valid, return 'No changes needed'. In only TWO sentences."
    )


class InferenceValidationResponseWithClaimIndex(InferenceValidationResponse):
    claim_index: int = Field(
        description="The index of the claim that is being validated"
    )
    chunk_index: int = Field(
        description="The index of the chunk that contains the claim"
    )


_inference_validation_prompt = ChatPromptTemplate.from_template(
    """
## Task
You are a inference validator using the Toulmin model of argumentation. You will receive the full document (context) and a specific chunk. Validate the inference of the chunk and, when possible, identify Toulmin elements for each claim.

- If a Toulmin element is not present, return an empty list for that element. For the warrant expression, return one of: "stated", "implied", or "none".
- If the chunk of text is a bibliographic entry (usually found in the references or bibliography section of the full document), do not consider it as having claims.
- If the chunk of text does not contain any argumentative content, do not consider it as having claims.

## Toulmin Definitions (concise)
- Claim: the assertion or conclusion to be established and whose validity is being determined.
- Data/Grounds: evidence or facts that support the claim.
- Warrant: the assumption or principle that connects data to claim; it may be stated explicitly or implied implicitly. Follows from the domain context or related references.
- Qualifier: words/phrases indicating the strength/scope of the claim (e.g., "likely", "some", "many", "in most cases").
- Rebuttal: acknowledged exceptions or counter-arguments to the claim.
- Backing: additional support that justifies the warrant (e.g., theories, principles, authorities, or methodological reasons).

Reference: Purdue OWL - Toulmin Argument (for definitions and orientation): https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html

{domain_context}

{audience_context}

## Important Instructions
- Focus only on content in the provided chunk when validating the inference; use the full document only for context/clarification.
- Validate the inference of the chunk. If the inference is not valid, return an empty list.
- For the identified claim, specify the following Toulmin elements:
  - "data": list specific evidence from the chunk that supports the claim (quoted or paraphrased).
  - "warrants": list the assumptions that link the data to the claim. If you infer a warrant from context, include it.
  - "warrant_expression": the expression of the warrant as "stated", "implied", or "none".
  - "qualifiers": list hedging or scope-limiting language associated with the claim.
  - "rebuttals": list acknowledged exceptions or counter-arguments present in the chunk.
  - "backing": list any additional support for the warrant (e.g., principles, cited studies, theoretical reasons) if present. Helps determine if the claim has been overstated or understated.
- In only TWO sentences, explain why you think the inference is valid or not. 
- In only TWO sentences, suggest an action to take if the inference is not valid. If the inference is valid, return 'No changes needed'.

## The full document that the chunk is a part of
```
{full_document}
```

## The paragraph of the original document that contains the chunk of text that we want to analyze
```
{paragraph}
```

## The chunk of text to analyze
```
{chunk}
```

## The claim to validate
```
{claim}
```
"""
)


class InferenceValidatorAgent(AgentProtocol):
    name = "Inference Validator"
    description = (
        "Validate the inference of a model using the toulmin model of argumentation."
    )

    def __init__(self):
        self.llm = init_chat_model(
            gpt_5_model.model_name,
            temperature=0.2,
            timeout=DEFAULT_LLM_TIMEOUT,
        ).with_structured_output(InferenceValidationResponseWithClaimIndex)

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: RunnableConfig = None,
    ) -> InferenceValidationResponseWithClaimIndex:
        messages = _inference_validation_prompt.format_messages(**prompt_kwargs)
        return await self.llm.ainvoke(messages, config=config)


inference_validator_agent = InferenceValidatorAgent()


# %%


if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()

    # Test code
    async def test_inference_validator():
        """Test the inference validator with sample data"""

        # Sample test data; now includes explicit claim_index and chunk_index for withClaimIndex structure
        test_data = {
            "full_document": """
            Renewable energy capacity has grown significantly in recent years. 
            Solar and wind power installations have increased by 40% since 2020.
            This growth is driven by declining costs and supportive government policies.
            However, challenges remain in grid integration and energy storage.
            """,
            "paragraph": """
            Solar and wind power installations have increased by 40% since 2020.
            This growth is driven by declining costs and supportive government policies.
            """,
            "chunk": "Solar and wind power installations have increased by 40% since 2020.",
            "claim": "Renewable energy capacity is expanding rapidly",
            "domain_context": "This is a report on energy infrastructure trends.",
            "audience_context": "The intended audience is policymakers and energy sector analysts.",
            "claim_index": 0,
            "chunk_index": 0,
        }

        # Create agent instance
        agent = InferenceValidatorAgent()

        # Test the validation
        print("Testing Inference Validator Agent")
        print("=" * 80)
        print(f"Claim: {test_data['claim']}")
        print(f"Chunk: {test_data['chunk']}")
        print("\nValidating...\n")

        result = await agent.ainvoke(test_data)

        print("Results:")
        print("-" * 80)
        print(f"Valid: {result.valid}")
        print(f"\nRationale:\n{result.rationale}")
        print(f"\nSuggested Action:\n{result.suggested_action}")
        print(f"Claim Index: {result.claim_index}")
        print(f"Chunk Index: {result.chunk_index}")
        print("=" * 80)

        return result

    async def test_invalid_inference():
        """Test with an invalid inference to see how the validator handles it"""

        test_data = {
            "full_document": """
            Solar panel efficiency has improved by 15% over the last decade.
            Manufacturing costs have decreased due to economies of scale.
            """,
            "paragraph": "Solar panel efficiency has improved by 15% over the last decade.",
            "chunk": "Solar panel efficiency has improved by 15% over the last decade.",
            "claim": "Solar panels will replace all fossil fuel energy by 2030",
            "domain_context": "This is a report on solar technology improvements.",
            "audience_context": "The intended audience is technology investors.",
            "claim_index": 0,
            "chunk_index": 0,
        }

        agent = InferenceValidatorAgent()

        print("\nTesting Invalid Inference")
        print("=" * 80)
        print(f"Claim: {test_data['claim']}")
        print(f"Chunk: {test_data['chunk']}")
        print("\nValidating...\n")

        result = await agent.ainvoke(test_data)

        print("Results:")
        print("-" * 80)
        print(f"Valid: {result.valid}")
        print(f"\nRationale:\n{result.rationale}")
        print(f"\nSuggested Action:\n{result.suggested_action}")
        print(f"Claim Index: {result.claim_index}")
        print(f"Chunk Index: {result.chunk_index}")
        print("=" * 80)

        return result

    print("\n🔍 Running Inference Validator Tests\n")

    # Run valid inference test
    result = asyncio.run(test_inference_validator())
    print("Valid Inference Test Result:")
    print(result.model_dump_json(indent=2))

    # Run invalid inference test
    result = asyncio.run(test_invalid_inference())
    print("Invalid Inference Test Result:")
    print(result.model_dump_json(indent=2))
