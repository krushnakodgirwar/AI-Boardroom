# from transformers import (
#     AutoTokenizer,
#     AutoModelForCausalLM,
#     BitsAndBytesConfig,
# )
# import torch


# class QwenLLM:
#     """
#     Local Qwen2.5-3B-Instruct language model.

#     Loads the model in 4-bit NF4 quantization using
#     bitsandbytes so it can run on a 4 GB RTX 3050.

#     No LoRA.
#     No PEFT.
#     No external API.
#     """

#     MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

#     def __init__(self):

#         print("Initializing Qwen2.5-3B-Instruct...")

#         # ==================================================
#         # DEVICE
#         # ==================================================

#         if not torch.cuda.is_available():

#             raise RuntimeError(
#                 "CUDA GPU is required for the 4-bit Qwen3B "
#                 "configuration."
#             )

#         self.device = "cuda"

#         print("Device: CUDA")

#         print(
#             f"GPU: {torch.cuda.get_device_name(0)}"
#         )

#         # ==================================================
#         # TOKENIZER
#         # ==================================================

#         print("Loading Qwen tokenizer...")

#         self.tokenizer = AutoTokenizer.from_pretrained(
#             self.MODEL_NAME
#         )

#         # ==================================================
#         # 4-BIT CONFIGURATION
#         # ==================================================

#         print("Configuring 4-bit NF4 quantization...")

#         self.quantization_config = BitsAndBytesConfig(
#             load_in_4bit=True,
#             bnb_4bit_quant_type="nf4",
#             bnb_4bit_use_double_quant=True,
#             bnb_4bit_compute_dtype=torch.float16,
#         )

#         # ==================================================
#         # MODEL
#         # ==================================================

#         print("Loading Qwen2.5-3B-Instruct in 4-bit...")

#         self.model = AutoModelForCausalLM.from_pretrained(
#             self.MODEL_NAME,
#             quantization_config=self.quantization_config,
#             device_map="auto",
#         )

#         # Evaluation mode
#         self.model.eval()

#         print(
#             "Qwen2.5-3B-Instruct 4-bit loaded successfully!"
#         )

#         # ==================================================
#         # MODEL DEVICE
#         # ==================================================

#         print(
#             f"Model device: "
#             f"{self.model.device}"
#         )

#         # ==================================================
#         # CONTEXT LENGTH
#         # ==================================================

#         self.max_context_tokens = (
#             self.model.config.max_position_embeddings
#         )

#         print(
#             f"Maximum context tokens: "
#             f"{self.max_context_tokens}"
#         )

#     # ======================================================
#     # GENERATE
#     # ======================================================

#     def generate(
#         self,
#         system_prompt,
#         user_prompt,
#         max_new_tokens=450
#     ):
#         """
#         Generate a deterministic response.

#         Uses greedy decoding instead of random sampling.
#         """

#         # ==================================================
#         # CHAT MESSAGES
#         # ==================================================

#         messages = [
#             {
#                 "role": "system",
#                 "content": system_prompt
#             },
#             {
#                 "role": "user",
#                 "content": user_prompt
#             }
#         ]

#         # ==================================================
#         # CHAT TEMPLATE
#         # ==================================================

#         prompt = self.tokenizer.apply_chat_template(
#             messages,
#             tokenize=False,
#             add_generation_prompt=True
#         )

#         # ==================================================
#         # TOKENIZE
#         # ==================================================

#         inputs = self.tokenizer(
#             prompt,
#             return_tensors="pt",
#             truncation=True,
#             max_length=self.max_context_tokens
#         )

#         # Move inputs to CUDA.
#         #
#         # The model itself is placed automatically by
#         # device_map="auto".

#         inputs = {
#             key: value.to(self.device)
#             for key, value in inputs.items()
#         }

#         # ==================================================
#         # PROMPT TOKEN COUNT
#         # ==================================================

#         prompt_tokens = (
#             inputs["input_ids"].shape[1]
#         )

#         print(
#             f"Prompt tokens: {prompt_tokens}"
#         )

#         # ==================================================
#         # AVAILABLE CONTEXT
#         # ==================================================

#         available_tokens = (
#             self.max_context_tokens
#             - prompt_tokens
#         )

#         if available_tokens <= 0:

#             raise ValueError(
#                 "Prompt is too large for the model "
#                 "context window."
#             )

#         actual_max_new_tokens = min(
#             max_new_tokens,
#             available_tokens
#         )

#         print(
#             f"Generation limit: "
#             f"{actual_max_new_tokens} tokens"
#         )

#         # ==================================================
#         # GENERATION
#         # ==================================================

#         with torch.inference_mode():

#             output = self.model.generate(
#                 **inputs,

#                 max_new_tokens=actual_max_new_tokens,

#                 # Deterministic generation
#                 do_sample=False,

#                 # Faster generation
#                 use_cache=True,
#                 # Static KV cache for faster repeated generation
#                 cache_implementation="static",

#                 eos_token_id=(
#                     self.tokenizer.eos_token_id
#                 ),

#                 pad_token_id=(
#                     self.tokenizer.eos_token_id
#                 )
#             )

#         # ==================================================
#         # REMOVE ORIGINAL PROMPT
#         # ==================================================

#         generated_tokens = output[
#             0,
#             prompt_tokens:
#         ]

#         # ==================================================
#         # DECODE
#         # ==================================================

#         response = self.tokenizer.decode(
#             generated_tokens,
#             skip_special_tokens=True
#         )

#         return response.strip()










from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
import torch
import time


class QwenLLM:
    """
    Local Qwen2.5-3B-Instruct language model.

    Configuration:
    - 4-bit NF4 quantization
    - CUDA GPU
    - PyTorch SDPA attention
    - Static KV cache
    - Inference mode

    No LoRA.
    No PEFT.
    No external API.
    """

    MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

    def __init__(self):

        print("Initializing Qwen2.5-3B-Instruct...")

        # ==================================================
        # DEVICE
        # ==================================================

        if not torch.cuda.is_available():

            raise RuntimeError(
                "CUDA GPU is required for the 4-bit Qwen3B "
                "configuration."
            )

        self.device = "cuda"

        print("Device: CUDA")

        print(
            f"GPU: {torch.cuda.get_device_name(0)}"
        )

        # ==================================================
        # TOKENIZER
        # ==================================================

        print("Loading Qwen tokenizer...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL_NAME
        )

        # ==================================================
        # 4-BIT CONFIGURATION
        # ==================================================

        print("Configuring 4-bit NF4 quantization...")

        self.quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

        # ==================================================
        # MODEL
        # ==================================================

        print(
            "Loading Qwen2.5-3B-Instruct in 4-bit..."
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_NAME,
            quantization_config=self.quantization_config,
            device_map="auto",

            # ==================================================
            # PYTORCH SDPA ATTENTION
            # ==================================================

            attn_implementation="sdpa",
        )

        # ==================================================
        # EVALUATION MODE
        # ==================================================

        self.model.eval()

        print(
            "Qwen2.5-3B-Instruct 4-bit loaded successfully!"
        )

        print(
            "Attention implementation: SDPA"
        )

        # ==================================================
        # MODEL DEVICE
        # ==================================================

        print(
            f"Model device: "
            f"{self.model.device}"
        )

        # ==================================================
        # CONTEXT LENGTH
        # ==================================================

        self.max_context_tokens = (
            self.model.config.max_position_embeddings
        )

        print(
            f"Maximum context tokens: "
            f"{self.max_context_tokens}"
        )

        # ==================================================
        # CUDA INFORMATION
        # ==================================================

        if torch.cuda.is_available():

            print(
                f"CUDA device: "
                f"{torch.cuda.get_device_name(0)}"
            )

            print(
                f"CUDA memory allocated: "
                f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB"
            )

            print(
                f"CUDA memory reserved: "
                f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB"
            )

    # ======================================================
    # GENERATE
    # ======================================================

    def generate(
        self,
        system_prompt,
        user_prompt,
        max_new_tokens=450
    ):
        """
        Generate a deterministic response.

        Uses:
        - Greedy decoding
        - SDPA attention
        - KV cache
        - Static KV cache
        - PyTorch inference mode

        Also measures generation performance.
        """

        # ==================================================
        # CHAT MESSAGES
        # ==================================================

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        # ==================================================
        # CHAT TEMPLATE
        # ==================================================

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # ==================================================
        # TOKENIZE
        # ==================================================

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_context_tokens
        )

        # ==================================================
        # MOVE INPUTS TO CUDA
        # ==================================================

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        # ==================================================
        # PROMPT TOKEN COUNT
        # ==================================================

        prompt_tokens = (
            inputs["input_ids"].shape[1]
        )

        print(
            f"Prompt tokens: {prompt_tokens}"
        )

        # ==================================================
        # AVAILABLE CONTEXT
        # ==================================================

        available_tokens = (
            self.max_context_tokens
            - prompt_tokens
        )

        if available_tokens <= 0:

            raise ValueError(
                "Prompt is too large for the model "
                "context window."
            )

        actual_max_new_tokens = min(
            max_new_tokens,
            available_tokens
        )

        print(
            f"Generation limit: "
            f"{actual_max_new_tokens} tokens"
        )

        

        # ==================================================
        # CUDA SYNCHRONIZATION
        # ==================================================

        if torch.cuda.is_available():

            torch.cuda.synchronize()

        # ==================================================
        # START TIMER
        # ==================================================

        start_time = time.perf_counter()

        # ==================================================
        # GENERATION
        # ==================================================

        with torch.inference_mode():

            output = self.model.generate(
                **inputs,

                # Maximum number of new tokens
                max_new_tokens=actual_max_new_tokens,

                # ==================================================
                # DETERMINISTIC GENERATION
                # ==================================================

                do_sample=False,

                # ==================================================
                # KV CACHE
                # ==================================================

                use_cache=True,


                

                # ==================================================
                # EOS TOKEN
                # ==================================================

                eos_token_id=(
                    self.tokenizer.eos_token_id
                ),

                # ==================================================
                # PAD TOKEN
                # ==================================================

                pad_token_id=(
                    self.tokenizer.eos_token_id
                )
            )

       

        # ==================================================
        # END TIMER
        # ==================================================

        generation_time = (
            time.perf_counter() - start_time
        )

        # ==================================================
        # GENERATED TOKEN COUNT
        # ==================================================

        generated_token_count = (
            output.shape[1] - prompt_tokens
        )

        # ==================================================
        # TOKENS PER SECOND
        # ==================================================

        if generation_time > 0:

            tokens_per_second = (
                generated_token_count
                / generation_time
            )

        else:

            tokens_per_second = 0

        # ==================================================
        # PERFORMANCE LOG
        # ==================================================

        print(
            "----------------------------------------"
        )

        print(
            f"Generated tokens: "
            f"{generated_token_count}"
        )

        print(
            f"Generation time: "
            f"{generation_time:.2f} seconds"
        )

        print(
            f"Generation speed: "
            f"{tokens_per_second:.2f} tokens/sec"
        )

        print(
            "----------------------------------------"
        )

        # ==================================================
        # CUDA MEMORY AFTER GENERATION
        # ==================================================

        if torch.cuda.is_available():

            print(
                f"CUDA memory allocated after generation: "
                f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB"
            )

        # ==================================================
        # REMOVE ORIGINAL PROMPT
        # ==================================================

        generated_tokens = output[
            0,
            prompt_tokens:
        ]

        # ==================================================
        # DECODE
        # ==================================================

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )

        return response.strip()